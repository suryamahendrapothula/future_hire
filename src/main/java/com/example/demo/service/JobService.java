package com.example.demo.service;

import com.example.demo.entity.Job;
import com.example.demo.entity.User;

import java.util.List;

public interface JobService {

    Job saveJob(Job job);

    List<Job> getAllJobs();

    List<Job> getActiveJobs();

    Job getJobById(Long id);

    void deleteJob(Long id);
    List<Job> getJobsByRecruiter(User recruiter);
    List<Job> searchJobs(User recruiter, String keyword);
    void toggleJobStatus(Long jobId);

}