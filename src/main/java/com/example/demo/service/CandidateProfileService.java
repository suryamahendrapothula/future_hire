package com.example.demo.service;

import com.example.demo.entity.CandidateProfile;
import com.example.demo.entity.User;

public interface CandidateProfileService {

    CandidateProfile getProfile(User user);

    CandidateProfile saveProfile(CandidateProfile profile);

}