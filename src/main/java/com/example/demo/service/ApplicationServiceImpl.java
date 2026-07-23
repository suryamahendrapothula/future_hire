package com.example.demo.service;

import org.springframework.stereotype.Service;

import com.example.demo.entity.Application;
import com.example.demo.entity.Job;
import com.example.demo.entity.User;
import com.example.demo.repository.ApplicationRepository;
import java.util.List;

@Service
public class ApplicationServiceImpl implements ApplicationService {
    private static final String APPLICATION_NOT_FOUND = "Application not found";

    private final ApplicationRepository applicationRepository;

    public ApplicationServiceImpl(ApplicationRepository applicationRepository) {
        this.applicationRepository = applicationRepository;
    }

    @Override
    public Application apply(User candidate, Job job) {

    	if (applicationRepository.findByCandidateAndJob(candidate, job).isPresent()) {
    	    return null;
    	}

        Application application = new Application();
        application.setCandidate(candidate);
        application.setJob(job);
        application.setStatus("Applied");

        return applicationRepository.save(application);
    }
    @Override
    public List<Application> getApplicationsByJob(Job job) {
        return applicationRepository.findByJob(job);
    }
    @Override
    public void shortlist(Long applicationId) {

        Application application = applicationRepository.findById(applicationId)
                .orElseThrow(() -> new RuntimeException(APPLICATION_NOT_FOUND));

        application.setStatus("Shortlisted");

        applicationRepository.save(application);
    }
    @Override
    public void reject(Long applicationId) {

        Application application = applicationRepository.findById(applicationId)
                .orElseThrow(() -> new RuntimeException(APPLICATION_NOT_FOUND));

        application.setStatus("Rejected");

        applicationRepository.save(application);
    }
    @Override
    public List<Application> getApplicationsByCandidate(User candidate) {

        return applicationRepository.findByCandidate(candidate);
    }
    @Override
    public Application getApplicationById(Long id) {

        return applicationRepository.findById(id)
                .orElseThrow(() -> new RuntimeException(APPLICATION_NOT_FOUND));
    }
}