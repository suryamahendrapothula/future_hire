package com.example.demo.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {

    private final CustomLoginSuccessHandler successHandler;

    public SecurityConfig(CustomLoginSuccessHandler successHandler) {
        this.successHandler = successHandler;
    }

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {

        http

            .authorizeHttpRequests(auth -> auth
                .requestMatchers(
                        "/",
                        "/css/**",
                        "/js/**",
                        "/images/**",
                        "/candidate/register",
                        "/candidate/login",
                        "/recruiter/register",
                        "/recruiter/login"
                ).permitAll()

                .requestMatchers("/candidate/**")
                .hasRole("CANDIDATE")

                .requestMatchers("/recruiter/**")
                .hasRole("RECRUITER")

                .anyRequest()
                .authenticated()
            )

            .formLogin(form -> form
                .loginPage("/candidate/login")
                .loginProcessingUrl("/login")
                .successHandler(successHandler)
                .permitAll()
            )

            .logout(logout -> logout
                .logoutSuccessUrl("/")
            );

        return http.build();
    }
}