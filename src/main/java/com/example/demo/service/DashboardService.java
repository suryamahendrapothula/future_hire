package com.example.demo.service;

import java.util.Map;

import com.example.demo.entity.User;

public interface DashboardService {

    Map<String, Object> getCandidateDashboardStats(User user);
    Map<String, Object> getRecruiterDashboardStats(User recruiter);

}