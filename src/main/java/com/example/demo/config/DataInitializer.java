package com.example.demo.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import com.example.demo.entity.Role;
import com.example.demo.entity.User;
import com.example.demo.repository.UserRepository;

@Component
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Value("${app.default.recruiter.password}")
    private String defaultRecruiterPassword;

    public DataInitializer(UserRepository userRepository,PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public void run(String... args) {

        if (!userRepository.existsByEmail("hr@futurehire.com")) {

            User recruiter = new User();

            recruiter.setFullName("HR Manager");
            recruiter.setEmail("hr@futurehire.com");
            recruiter.setPassword(passwordEncoder.encode(defaultRecruiterPassword));
            recruiter.setRole(Role.ROLE_RECRUITER);
            recruiter.setEnabled(true);

            userRepository.save(recruiter);

        }

    }

}