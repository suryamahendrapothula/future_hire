package com.example.demo.controller;

import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

import com.example.demo.dto.RegisterRequest;
import com.example.demo.entity.User;
import com.example.demo.repository.UserRepository;
import com.example.demo.service.DashboardService;
import com.example.demo.service.UserService;

@Controller
public class RecruiterController {

	private final DashboardService dashboardService;
	private final UserRepository userRepository;
	private final UserService userService;

	public RecruiterController(DashboardService dashboardService, UserRepository userRepository,
			UserService userService) {

		this.dashboardService = dashboardService;
		this.userRepository = userRepository;
		this.userService = userService;
	}

	@GetMapping("/recruiter/login")
	public String recruiterLogin() {
		return "auth/recruiter-login";
	}

	@GetMapping("/recruiter/register")
	public String recruiterRegisterPage(Model model) {

		model.addAttribute("registerRequest", new RegisterRequest());

		return "auth/recruiter-register";
	}

	@PostMapping("/recruiter/register")
	public String recruiterRegister(@ModelAttribute RegisterRequest registerRequest) {

		userService.registerRecruiter(registerRequest);

		return "redirect:/recruiter/login";
	}

	@GetMapping("/recruiter/dashboard")
	public String recruiterDashboard(Authentication authentication, Model model) {

		User recruiter = userRepository.findByEmail(authentication.getName()).orElseThrow();

		model.addAttribute("stats", dashboardService.getRecruiterDashboardStats(recruiter));

		return "recruiter/dashboard";
	}
}