package com.example.demo.controller;

import com.example.demo.entity.Job;
import com.example.demo.service.JobService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import com.example.demo.entity.Application;
import com.example.demo.service.ApplicationService;
import java.util.List;
import com.example.demo.repository.ResumeRepository;
import com.example.demo.entity.Resume;
import org.springframework.security.core.Authentication;
import com.example.demo.entity.User;
import com.example.demo.repository.UserRepository;
import com.example.demo.entity.Role;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import java.nio.file.Path;
import java.nio.file.Paths;

import com.example.demo.entity.Interview;
import com.example.demo.entity.InterviewQuestion;
import com.example.demo.entity.InterviewAnswer;
import com.example.demo.repository.InterviewRepository;
import com.example.demo.repository.InterviewQuestionRepository;
import com.example.demo.repository.InterviewAnswerRepository;
import com.example.demo.exception.FileDownloadException;

@Controller
@RequestMapping("/recruiter/jobs")
public class JobController {
	private static final String REDIRECT_RECRUITER_JOBS =
        "redirect:/recruiter/jobs";

private static final String REDIRECT_UNAUTHORIZED =
        "redirect:/recruiter/jobs?error=Unauthorized";

	private final JobService jobService;
	private final ApplicationService applicationService;
	private final ResumeRepository resumeRepository;
	private final UserRepository userRepository;
	private final InterviewRepository interviewRepository;
	private final InterviewQuestionRepository interviewQuestionRepository;
	private final InterviewAnswerRepository interviewAnswerRepository;

	public JobController(JobService jobService, ApplicationService applicationService,
			ResumeRepository resumeRepository, UserRepository userRepository,
			InterviewRepository interviewRepository, InterviewQuestionRepository interviewQuestionRepository,
			InterviewAnswerRepository interviewAnswerRepository) {

		this.jobService = jobService;
		this.applicationService = applicationService;
		this.resumeRepository = resumeRepository;
		this.userRepository = userRepository;
		this.interviewRepository = interviewRepository;
		this.interviewQuestionRepository = interviewQuestionRepository;
		this.interviewAnswerRepository = interviewAnswerRepository;
	}

	@GetMapping("/new")
	public String createJobForm(Model model) {

		model.addAttribute("job", new Job());

		return "recruiter/create-job";
	}

	@PostMapping("/save")
	public String saveJob(@ModelAttribute("job") Job job,
	                      Authentication authentication) {

	    User recruiter = userRepository
	            .findByEmail(authentication.getName())
	            .orElseThrow();

	    job.setRecruiter(recruiter);

	    jobService.saveJob(job);

	    return "redirect:/recruiter/dashboard";
	}

	@GetMapping
	public String viewJobs(
	        @RequestParam(required = false) String keyword,
	        Authentication authentication,
	        Model model) {

	    User recruiter = userRepository
	            .findByEmail(authentication.getName())
	            .orElseThrow();

	    List<Job> jobs;

	    if (keyword != null && !keyword.trim().isEmpty()) {

	        jobs = jobService.searchJobs(recruiter, keyword);

	    } else {

	        jobs = jobService.getJobsByRecruiter(recruiter);
	    }

	    model.addAttribute("jobs", jobs);
	    model.addAttribute("keyword", keyword);

	    return "recruiter/jobs";
	}

	@GetMapping("/edit/{id}")
	public String editJob(@PathVariable Long id, Authentication authentication, Model model) {

		Job job = jobService.getJobById(id);
		if (isNotOwner(job, authentication)) {
			return REDIRECT_UNAUTHORIZED;
		}

		model.addAttribute("job", job);

		return "recruiter/create-job";
	}

	@GetMapping("/delete/{id}")
	public String deleteJob(@PathVariable Long id, Authentication authentication) {

		Job job = jobService.getJobById(id);
		if (isNotOwner(job, authentication)) {
			return REDIRECT_UNAUTHORIZED;
		}

		jobService.deleteJob(id);

		return REDIRECT_RECRUITER_JOBS;
	}

	@GetMapping("/{id}/applicants")
	public String viewApplicants(@PathVariable Long id, Authentication authentication, Model model) {

		Job job = jobService.getJobById(id);
		if (isNotOwner(job, authentication)) {
			return REDIRECT_UNAUTHORIZED;
		}

		List<Application> applications = applicationService.getApplicationsByJob(job);

		java.util.Map<Long, Interview> interviewMap = new java.util.HashMap<>();
		int completedCount = 0;
		int totalScoreSum = 0;

		for (Application app : applications) {
			interviewRepository.findByApplication(app).ifPresent(i -> interviewMap.put(app.getId(), i));
		}

		for (Interview i : interviewMap.values()) {
			if ("COMPLETED".equalsIgnoreCase(i.getStatus()) && i.getOverallScore() != null) {
				totalScoreSum += i.getOverallScore();
				completedCount++;
			}
		}

		double averageScore = completedCount > 0 ? (double) totalScoreSum / completedCount : 0.0;

		model.addAttribute("job", job);
		model.addAttribute("applications", applications);
		model.addAttribute("interviews", interviewMap);
		model.addAttribute("averageScore", String.format(java.util.Locale.US, "%.1f", averageScore));
		model.addAttribute("completedCount", completedCount);

		return "recruiter/applicants";
	}

	@GetMapping("/resume/{candidateId}")
	public String viewResume(@PathVariable Long candidateId, Model model) {

		Resume resume = resumeRepository.findByUserId(candidateId)
				.orElseThrow(() -> new RuntimeException("Resume not found"));

		model.addAttribute("resume", resume);

		return "recruiter/resume-details";
	}

	@GetMapping("/interview/{interviewId}")
	public String viewInterviewDetails(
			@PathVariable Long interviewId,
			Model model,
			Authentication authentication) {

		Interview interview = interviewRepository.findById(interviewId)
				.orElseThrow(() -> new RuntimeException("Interview not found"));

		if (isNotOwner(interview.getApplication().getJob(), authentication)) {
			return REDIRECT_UNAUTHORIZED;
		}

		List<InterviewQuestion> questions = interviewQuestionRepository.findByInterviewOrderByQuestionNumberAsc(interview);
		java.util.Map<Long, InterviewAnswer> answerMap = new java.util.HashMap<>();
		for (InterviewQuestion q : questions) {
			interviewAnswerRepository.findByQuestion(q).ifPresent(ans -> answerMap.put(q.getId(), ans));
		}

		model.addAttribute("interview", interview);
		model.addAttribute("questions", questions);
		model.addAttribute("answers", answerMap);

		return "recruiter/interview-details";
	}

	@GetMapping("/applications/{applicationId}/shortlist")
	public String shortlistApplication(@PathVariable Long applicationId, Authentication authentication) {

		Application application = applicationService.getApplicationById(applicationId);
		if (application == null || isNotOwner(application.getJob(), authentication)) {
			return REDIRECT_UNAUTHORIZED;
		}

		applicationService.shortlist(applicationId);

		return REDIRECT_RECRUITER_JOBS;
	}

	@GetMapping("/applications/{applicationId}/reject")
	public String rejectApplication(@PathVariable Long applicationId, Authentication authentication) {

		Application application = applicationService.getApplicationById(applicationId);
		if (application == null || isNotOwner(application.getJob(), authentication)) {
			return REDIRECT_UNAUTHORIZED;
		}

		applicationService.reject(applicationId);

		return REDIRECT_RECRUITER_JOBS;
	}

	@GetMapping("/toggle/{id}")
	public String toggleJobStatus(@PathVariable Long id, Authentication authentication) {

		Job job = jobService.getJobById(id);
		if (isNotOwner(job, authentication)) {
			return REDIRECT_UNAUTHORIZED;
		}

		jobService.toggleJobStatus(id);

		return REDIRECT_RECRUITER_JOBS;
	}

	@GetMapping("/resume/download/{resumeId}")
	public ResponseEntity<Resource> downloadResume(
			@PathVariable Long resumeId,
			Authentication authentication) {

		Resume resume = resumeRepository.findById(resumeId)
				.orElseThrow(() -> new RuntimeException("Resume not found"));

		User recruiter = userRepository.findByEmail(authentication.getName())
				.orElseThrow(() -> new RuntimeException("User not found"));

		boolean isAuthorized = recruiter.getRole() == Role.ROLE_RECRUITER && 
				applicationService.getApplicationsByCandidate(resume.getUser()).stream()
				.anyMatch(app -> app.getJob().getRecruiter() != null && 
						app.getJob().getRecruiter().getId().equals(recruiter.getId()));

		if (!isAuthorized) {
			return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
		}

		try {
			Path filePath = Paths.get(resume.getFilePath());
			Resource resource = new UrlResource(filePath.toUri());

			if (resource.exists() || resource.isReadable()) {
				String contentType = "application/pdf";
				return ResponseEntity.ok()
						.contentType(MediaType.parseMediaType(contentType))
						.header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + resume.getFileName() + "\"")
						.body(resource);
			} else {
				throw new FileDownloadException("Could not read file: " + resume.getFileName());
			}
		} catch (Exception e) {
			throw new FileDownloadException("Error occurred while downloading file: "+ e.getMessage(), e);
		}
	}

	private boolean isNotOwner(Job job, Authentication authentication) {
		if (job == null || authentication == null) return true;
		User recruiter = userRepository.findByEmail(authentication.getName()).orElse(null);
		return recruiter == null || job.getRecruiter() == null || !job.getRecruiter().getId().equals(recruiter.getId());
	}

}