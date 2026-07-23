package com.example.demo.controller;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import com.example.demo.entity.Application;
import com.example.demo.entity.Interview;
import com.example.demo.service.ApplicationService;
import com.example.demo.service.InterviewService;

import java.time.LocalDateTime;
import java.util.List;
import com.example.demo.entity.InterviewQuestion;
import com.example.demo.repository.InterviewRepository;
import com.example.demo.repository.ResumeRepository;
import com.example.demo.entity.Resume;

@Controller
@RequestMapping("/candidate/interview")
public class InterviewController {

    private static final String INTERVIEW = "interview";


    private final InterviewService interviewService;
    private final ApplicationService applicationService;
    private final InterviewRepository interviewRepository;
    private final ResumeRepository resumeRepository;

    public InterviewController(
            InterviewService interviewService,
            ApplicationService applicationService,
            InterviewRepository interviewRepository,
            ResumeRepository resumeRepository) {

        this.interviewService = interviewService;
        this.applicationService = applicationService;
        this.interviewRepository = interviewRepository;
        this.resumeRepository = resumeRepository;
    }

    @GetMapping("/{applicationId}")
    public String startInterview(@PathVariable Long applicationId,
                                 Model model) {

        Application application =
                applicationService.getApplicationById(applicationId);

        Resume resume = resumeRepository.findByUserId(application.getCandidate().getId()).orElse(null);
        if (resume == null) {
            return "redirect:/candidate/dashboard?error=MissingResume";
        }

        Interview interview =
                interviewService.startInterview(application);

        model.addAttribute(INTERVIEW, interview);
        model.addAttribute("applicationId", applicationId);

        return "candidate/interview";
    }
    @GetMapping("/{applicationId}/start")
    public String beginInterview(@PathVariable Long applicationId,
                                 Model model) {

        Application application =
                applicationService.getApplicationById(applicationId);

        Resume resume = resumeRepository.findByUserId(application.getCandidate().getId()).orElse(null);
        if (resume == null) {
            return "redirect:/candidate/dashboard?error=MissingResume";
        }

        Interview interview =
                interviewService.startInterview(application);
        if (interview.getAiInterviewId() == null) {
            interviewService.initializeQuestions(interview);
        }

        List<InterviewQuestion> questions =
                interviewService.getQuestions(interview);

        model.addAttribute("question", questions.get(0));

        model.addAttribute(INTERVIEW, interview);
        model.addAttribute("application", application);

        return "candidate/interview-session";
    }
    @PostMapping("/submit")
    public String submitAnswer(
            @RequestParam Long questionId,
            @RequestParam String answer,
            Model model) {

        InterviewQuestion currentQuestion =
                interviewService.getQuestionById(questionId);

        interviewService.saveAnswer(currentQuestion, answer);

        Interview interview = currentQuestion.getInterview();

        InterviewQuestion nextQuestion =
                interviewService.getNextQuestion(
                        interview,
                        currentQuestion.getQuestionNumber());

        if (nextQuestion == null) {

            interview.setStatus("COMPLETED");
            interview.setCompletedAt(LocalDateTime.now());

            interviewService.endInterview(interview);
            interviewRepository.save(interview);

            model.addAttribute(INTERVIEW, interview);

            return "candidate/interview-result";
        }

        model.addAttribute(INTERVIEW, interview);
        model.addAttribute("question", nextQuestion);

        return "candidate/interview-session";
    }

}