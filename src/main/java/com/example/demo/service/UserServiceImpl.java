package com.example.demo.service;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.example.demo.dto.RegisterRequest;
import com.example.demo.entity.Role;
import com.example.demo.entity.User;
import com.example.demo.repository.UserRepository;

import com.example.demo.exception.UserAlreadyExistsException;

@Service
public class UserServiceImpl implements UserService {

	private final UserRepository userRepository;
	private final PasswordEncoder passwordEncoder;

	public UserServiceImpl(UserRepository userRepository, PasswordEncoder passwordEncoder) {

		this.userRepository = userRepository;
		this.passwordEncoder = passwordEncoder;
	}

	@Override
	public void registerCandidate(RegisterRequest request) {
		registerUser(request, Role.ROLE_CANDIDATE);
	}

	@Override
	public void registerRecruiter(RegisterRequest request) {
		registerUser(request, Role.ROLE_RECRUITER);
	}

	private void registerUser(RegisterRequest request, Role role) {

		if (userRepository.existsByEmail(request.getEmail())) {
			throw new UserAlreadyExistsException("Email already exists: " + request.getEmail());
		}

		User user = new User();

		user.setFullName(request.getFullName());
		user.setEmail(request.getEmail());
		user.setPassword(passwordEncoder.encode(request.getPassword()));
		user.setRole(role);
		user.setEnabled(true);

		userRepository.save(user);
	}
}
