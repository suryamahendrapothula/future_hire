package com.example.demo.service;

import org.springframework.web.multipart.MultipartFile;
import com.example.demo.exception.ResumeUploadException;

public interface ResumeService {

    void uploadResume(MultipartFile file, String email) throws ResumeUploadException;

}