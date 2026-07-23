package com.example.demo.controller;

import java.security.Principal;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.multipart.MultipartFile;

import com.example.demo.service.ResumeService;

@Controller
@RequestMapping("/candidate")
public class ResumeController {
	private final ResumeService resumeService;

	public ResumeController(ResumeService resumeService) {
	    this.resumeService = resumeService;
	}

    @GetMapping("/resume")
    public String resumePage() {
        return "candidate/resume-upload";
    }
    @PostMapping("/resume/upload")
    public String uploadResume(
            @RequestParam("file") MultipartFile file,
            Principal principal) {

    	String email = principal.getName();

        resumeService.uploadResume(file, email);

        return "redirect:/candidate/dashboard";
    }
    

}