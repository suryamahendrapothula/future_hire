package com.example.demo.service;

import com.example.demo.dto.RegisterRequest;

public interface UserService {

    void registerCandidate(RegisterRequest request);
    void registerRecruiter(RegisterRequest request);

}