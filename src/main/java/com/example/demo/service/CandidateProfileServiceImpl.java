package com.example.demo.service;

import org.springframework.stereotype.Service;

import com.example.demo.entity.CandidateProfile;
import com.example.demo.entity.User;
import com.example.demo.repository.CandidateProfileRepository;

@Service
public class CandidateProfileServiceImpl implements CandidateProfileService {

    private final CandidateProfileRepository profileRepository;

    public CandidateProfileServiceImpl(CandidateProfileRepository profileRepository) {
        this.profileRepository = profileRepository;
    }

    @Override
    public CandidateProfile getProfile(User user) {

        return profileRepository.findByUser(user).orElseGet(() -> {

            CandidateProfile profile = new CandidateProfile();
            profile.setUser(user);

            return profileRepository.save(profile);
        });
    }

    @Override
    public CandidateProfile saveProfile(CandidateProfile profile) {
        return profileRepository.save(profile);
    }
}