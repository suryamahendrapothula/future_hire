package com.example.demo.controller;

import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import com.example.demo.entity.CandidateProfile;
import com.example.demo.entity.User;
import com.example.demo.repository.UserRepository;
import com.example.demo.service.CandidateProfileService;

@Controller
@RequestMapping("/candidate/profile")
public class CandidateProfileController {

    private final CandidateProfileService profileService;
    private final UserRepository userRepository;

    public CandidateProfileController(CandidateProfileService profileService,
                                      UserRepository userRepository) {
        this.profileService = profileService;
        this.userRepository = userRepository;
    }

    @GetMapping
    public String viewProfile(Authentication authentication, Model model) {

        User user = userRepository
                .findByEmail(authentication.getName())
                .orElseThrow();

        CandidateProfile profile = profileService.getProfile(user);

        model.addAttribute("profile", profile);

        return "candidate/profile";
    }
    @GetMapping("/edit")
    public String editProfile(Authentication authentication, Model model) {

        User user = userRepository
                .findByEmail(authentication.getName())
                .orElseThrow();

        CandidateProfile profile = profileService.getProfile(user);

        model.addAttribute("profile", profile);

        return "candidate/edit-profile";
    }
    @PostMapping("/edit")
    public String updateProfile(@ModelAttribute CandidateProfile profile,
                                Authentication authentication) {

        User user = userRepository
                .findByEmail(authentication.getName())
                .orElseThrow();

        profile.setUser(user);

        profileService.saveProfile(profile);

        return "redirect:/candidate/profile";
    }
}