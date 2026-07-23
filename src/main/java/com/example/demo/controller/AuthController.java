package com.example.demo.controller;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import com.example.demo.dto.RegisterRequest;
import com.example.demo.service.UserService;

@Controller
@RequestMapping("/candidate")
public class AuthController {

    private final UserService userService;

    public AuthController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/login")
    public String login() {
        return "auth/candidate-login";
    }

    @GetMapping("/register")
    public String registerPage(Model model) {
        model.addAttribute("registerRequest", new RegisterRequest());
        return "auth/candidate-register";
    }

    @PostMapping("/register")
    public String register(@ModelAttribute RegisterRequest registerRequest) {

        userService.registerCandidate(registerRequest);

        return "redirect:/candidate/login";
    }

}
