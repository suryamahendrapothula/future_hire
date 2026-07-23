package com.example.demo.service;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;

import org.apache.tika.Tika;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import com.example.demo.entity.Resume;
import com.example.demo.entity.User;
import com.example.demo.repository.ResumeRepository;
import com.example.demo.repository.UserRepository;

import javax.transaction.Transactional;

import com.example.demo.entity.Skill;
import com.example.demo.entity.CandidateSkill;
import com.example.demo.repository.SkillRepository;
import com.example.demo.repository.CandidateSkillRepository;
import com.example.demo.dto.AIResponse;
import com.example.demo.exception.ResumeUploadException;

@Service
public class ResumeServiceImpl implements ResumeService {
	private final SkillRepository skillRepository;
	private final CandidateSkillRepository candidateSkillRepository;

    private final ResumeRepository resumeRepository;
    private final UserRepository userRepository;
    private final AIService aiService;
    private final ResumeAnalysisService resumeAnalysisService;

    public ResumeServiceImpl(
            ResumeRepository resumeRepository,
            UserRepository userRepository,
            SkillRepository skillRepository,
            CandidateSkillRepository candidateSkillRepository,
            AIService aiService,
            ResumeAnalysisService resumeAnalysisService) {

        this.resumeRepository = resumeRepository;
        this.userRepository = userRepository;
        this.skillRepository = skillRepository;
        this.candidateSkillRepository = candidateSkillRepository;
        this.aiService = aiService;
        this.resumeAnalysisService = resumeAnalysisService;
    }
    @Override
    @Transactional
    public void uploadResume(MultipartFile file, String email) throws ResumeUploadException {

        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new ResumeUploadException("User not found with email: " + email));

        String uploadDir = "uploads";

        File directory = new File(uploadDir);

        if (!directory.exists()) {
            directory.mkdirs();
        }

        Path path = Paths.get(uploadDir, file.getOriginalFilename());

        try {
            Files.copy(
                    file.getInputStream(),
                    path,
                    StandardCopyOption.REPLACE_EXISTING
            );
        } catch (Exception e) {
            throw new ResumeUploadException("Failed to save uploaded file: " + e.getMessage(), e);
        }

        Resume resume = resumeRepository.findByUserId(user.getId()).orElse(null);

        if (resume == null) {
            resume = new Resume();
        }

        resume.setFileName(file.getOriginalFilename());
        resume.setFilePath(path.toString());

        Tika tika = new Tika();

        String extractedText;
        try {
            extractedText = tika.parseToString(path);
        } catch (Exception e) {
            throw new ResumeUploadException("Failed to extract text from resume: " + e.getMessage(), e);
        }

        resume.setExtractedText(extractedText);

        // AI Resume Analysis with local fallback
        AIResponse response = null;
        try {
            response = aiService.analyzeResume(extractedText);
        } catch (Exception e) {
            // Local fallback using ResumeAnalysisService
            com.example.demo.dto.ResumeAnalysis localAnalysis = resumeAnalysisService.analyze(extractedText);
            response = new AIResponse();
            response.setScore(50 + Math.min(localAnalysis.getSkills().size() * 5, 40));
            response.setSummary("Local Analysis: live AI evaluation server offline. Extracted text successfully parsed.");
            response.setExperienceLevel(localAnalysis.getExperienceYears() > 0 ? localAnalysis.getExperienceYears() + " Years" : "Fresher");
            response.setStrengths(java.util.List.of("Matches skills found in our taxonomy."));
            response.setWeaknesses(java.util.List.of("Connect AI server for weakness evaluation."));
            response.setJobRoles(java.util.List.of("Software Developer", "IT Professional"));
            response.setSkills(localAnalysis.getSkills());
        }

        resume.setAiScore(response.getScore());
        resume.setSummary(response.getSummary());

        resume.setExperienceLevel(response.getExperienceLevel());

        resume.setStrengths(
                String.join("\n", response.getStrengths() != null ? response.getStrengths() : java.util.Collections.emptyList()));

        resume.setWeaknesses(
                String.join("\n", response.getWeaknesses() != null ? response.getWeaknesses() : java.util.Collections.emptyList()));

        resume.setJobRoles(
                String.join("\n", response.getJobRoles() != null ? response.getJobRoles() : java.util.Collections.emptyList()));

        candidateSkillRepository.deleteByUser(user);

        if (response.getSkills() != null) {
            for (String skillName : response.getSkills()) {

                Skill skill = skillRepository.findByName(skillName)
                        .orElseGet(() -> {

                            Skill newSkill = new Skill();
                            newSkill.setName(skillName);

                            return skillRepository.save(newSkill);
                        });

                CandidateSkill candidateSkill = new CandidateSkill();
                candidateSkill.setUser(user);
                candidateSkill.setSkill(skill);

                candidateSkillRepository.save(candidateSkill);
            }
        }

        resume.setUser(user);

        resumeRepository.save(resume);
}
}