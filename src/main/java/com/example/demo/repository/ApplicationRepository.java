package com.example.demo.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.demo.entity.Application;
import com.example.demo.entity.Job;
import com.example.demo.entity.User;
import java.util.List;

public interface ApplicationRepository extends JpaRepository<Application, Long> {

    Optional<Application> findByCandidateAndJob(User candidate, Job job);
    List<Application> findByJob(Job job);
    List<Application> findByCandidate(User candidate);
    long countByCandidate(User candidate);
    long countByJobRecruiter(User recruiter);
    long countByJobRecruiterAndStatus(
            User recruiter,
            String status);

}