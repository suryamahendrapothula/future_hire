package com.example.demo.service;

import java.util.HashMap;
import java.util.Map;

import org.springframework.stereotype.Service;

import com.example.demo.entity.User;
import com.example.demo.repository.ApplicationRepository;
import com.example.demo.repository.InterviewRepository;
import com.example.demo.repository.JobRepository;
import com.example.demo.repository.ResumeRepository;


@Service
public class DashboardServiceImpl implements DashboardService {

    private final ApplicationRepository applicationRepository;
    private final InterviewRepository interviewRepository;
    private final ResumeRepository resumeRepository;
    private final JobRepository jobRepository;

    public DashboardServiceImpl(
            ApplicationRepository applicationRepository,
            InterviewRepository interviewRepository,
            ResumeRepository resumeRepository,
            JobRepository jobRepository) {

        this.applicationRepository = applicationRepository;
        this.interviewRepository = interviewRepository;
        this.resumeRepository = resumeRepository;
        this.jobRepository = jobRepository;
    }

    @Override
    public Map<String, Object> getCandidateDashboardStats(User user) {

        Map<String, Object> stats = new HashMap<>();

        stats.put("applications",
                applicationRepository.countByCandidate(user));

        stats.put("interviews",
                interviewRepository.countByApplicationCandidate(user));

        stats.put("resumeUploaded",
                resumeRepository.existsByUser(user));

        return stats;
    }
    @Override
    public Map<String, Object> getRecruiterDashboardStats(User recruiter) {

        Map<String, Object> stats = new HashMap<>();

        stats.put("jobs",
                jobRepository.countByRecruiter(recruiter));

        stats.put("applications",
                applicationRepository.countByJobRecruiter(recruiter));

        stats.put("shortlisted",
                applicationRepository.countByJobRecruiterAndStatus(
                        recruiter,
                        "Shortlisted"));

        stats.put("rejected",
                applicationRepository.countByJobRecruiterAndStatus(
                        recruiter,
                        "Rejected"));

        stats.put("interviews",
                interviewRepository.countByApplicationJobRecruiter(recruiter));

        return stats;
    }
}