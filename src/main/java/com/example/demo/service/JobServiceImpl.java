package com.example.demo.service;

import com.example.demo.entity.Job;
import com.example.demo.entity.User;
import com.example.demo.repository.JobRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class JobServiceImpl implements JobService {

    private final JobRepository jobRepository;

    public JobServiceImpl(JobRepository jobRepository) {
        this.jobRepository = jobRepository;
    }

    @Override
    public Job saveJob(Job job) {
        return jobRepository.save(job);
    }

    @Override
    public List<Job> getAllJobs() {
        return jobRepository.findAll();
    }

    @Override
    public List<Job> getActiveJobs() {
        return jobRepository.findByActiveTrue();
    }

    @Override
    public Job getJobById(Long id) {
        return jobRepository.findById(id).orElse(null);
    }

    @Override
    public void deleteJob(Long id) {
        jobRepository.deleteById(id);
    }
    @Override
    public List<Job> getJobsByRecruiter(User recruiter) {

        return jobRepository.findByRecruiter(recruiter);
    }
    @Override
    public List<Job> searchJobs(User recruiter, String keyword) {

        return jobRepository.findByRecruiterAndTitleContainingIgnoreCase(
                recruiter,
                keyword);
    }
    @Override
    public void toggleJobStatus(Long jobId) {

        Job job = jobRepository.findById(jobId)
                .orElseThrow(() -> new RuntimeException("Job not found"));

        job.setActive(!job.isActive());

        jobRepository.save(job);
    }
}