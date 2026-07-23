package com.example.demo.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.demo.entity.Application;
import com.example.demo.entity.Interview;
import com.example.demo.entity.User;

public interface InterviewRepository extends JpaRepository<Interview, Long> {

    Optional<Interview> findByApplication(Application application);
    long countByApplicationCandidate(User candidate);
    long countByApplicationJobRecruiter(User recruiter);

}