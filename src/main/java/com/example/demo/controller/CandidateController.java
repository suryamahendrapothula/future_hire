package com.example.demo.controller;

import java.security.Principal;
import java.util.List;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import com.example.demo.entity.CandidateSkill;
import com.example.demo.entity.User;
import com.example.demo.repository.CandidateSkillRepository;
import com.example.demo.repository.ResumeRepository;
import com.example.demo.repository.UserRepository;
import com.example.demo.entity.Resume;
import com.example.demo.service.JobService;
import org.springframework.web.bind.annotation.PathVariable;
import com.example.demo.entity.Job;
import com.example.demo.service.ApplicationService;
import com.example.demo.service.DashboardService;
import com.example.demo.entity.Application;
import org.springframework.security.core.Authentication;

import com.example.demo.repository.InterviewRepository;
import com.example.demo.entity.Interview;
import java.util.Map;
import java.util.HashMap;

@Controller
@RequestMapping("/candidate")
public class CandidateController {
	
    private final CandidateSkillRepository candidateSkillRepository;
    private final UserRepository userRepository;
    private final ResumeRepository resumeRepository;
    private final JobService jobService;
    private final ApplicationService applicationService;
    private final DashboardService dashboardService;
    private final InterviewRepository interviewRepository;

    public CandidateController(
            CandidateSkillRepository candidateSkillRepository,
            UserRepository userRepository,
            ResumeRepository resumeRepository,
            JobService jobService,
            ApplicationService applicationService,
            DashboardService dashboardService,
            InterviewRepository interviewRepository) {
    	
    	this.jobService = jobService;
        this.candidateSkillRepository = candidateSkillRepository;
        this.userRepository = userRepository;
        this.resumeRepository = resumeRepository;
        this.applicationService = applicationService;
        this.dashboardService = dashboardService;
        this.interviewRepository = interviewRepository;
    }

    @GetMapping("/dashboard")
    public String dashboard(Model model, Principal principal) {

        User user = userRepository.findByEmail(principal.getName()).orElseThrow();
        Resume resume = resumeRepository.findByUserId(user.getId()).orElse(null);

        model.addAttribute("resume", resume);

        List<CandidateSkill> skills = candidateSkillRepository.findByUser(user);

        model.addAttribute("skills", skills);
        model.addAttribute("skillCount", skills.size());
        model.addAttribute("jobs", jobService.getActiveJobs());
        model.addAttribute(
                "stats",
                dashboardService.getCandidateDashboardStats(user));

        return "candidate/dashboard";
    }

    @GetMapping("/jobs/{id}")
    public String viewJob(@PathVariable Long id, Model model) {

        Job job = jobService.getJobById(id);

        model.addAttribute("job", job);

        return "candidate/job-details";
    }

    @GetMapping("/apply/{jobId}")
    public String applyJob(@PathVariable Long jobId, Principal principal) {

        User candidate = userRepository.findByEmail(principal.getName())
                .orElseThrow();

        Job job = jobService.getJobById(jobId);

        Application application = applicationService.apply(candidate, job);

        if (application == null) {
            return "redirect:/candidate/jobs/" + jobId + "?alreadyApplied";
        }

        return "redirect:/candidate/dashboard?applied";
    }

    @GetMapping("/applications")
    public String myApplications(Authentication authentication, Model model) {

    	User candidate = userRepository
    	        .findByEmail(authentication.getName())
    	        .orElseThrow();

        List<Application> applications =
                applicationService.getApplicationsByCandidate(candidate);

        Map<Long, Interview> interviewMap = new HashMap<>();
        for (Application app : applications) {
            interviewRepository.findByApplication(app).ifPresent(i -> interviewMap.put(app.getId(), i));
        }

        model.addAttribute("applications", applications);
        model.addAttribute("interviewMap", interviewMap);

        return "candidate/my-applications";
    }
}