package com.example.demo.service;

import com.example.demo.entity.Application;
import com.example.demo.entity.Job;
import com.example.demo.entity.User;
import java.util.List;

public interface ApplicationService {

    Application apply(User candidate, Job job);
    List<Application> getApplicationsByJob(Job job);
    void shortlist(Long applicationId);

    void reject(Long applicationId);
    List<Application> getApplicationsByCandidate(User candidate);
    Application getApplicationById(Long id);

}