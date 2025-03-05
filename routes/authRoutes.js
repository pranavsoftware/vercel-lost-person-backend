const express = require("express");
const jwt = require("jsonwebtoken");
const User = require("../models/User");
const sendRegistrationEmail = require("../utils/emailService");

const router = express.Router();
const jwtSecret = process.env.JWT_SECRET || "your_jwt_secret";

/**
 * @route POST /api/auth/register
 * @desc  Register a new user
 * @access Public
 */
router.post("/register", async (req, res) => {
    try {
        const { name, email, mobile, location, password } = req.body;

        // Check if user already exists
        let user = await User.findOne({ email });
        if (user) return res.status(400).json({ message: "❌ Email already exists" });

        console.log("🔑 Storing Plain Password:", password.trim()); // Debugging log

        // Store the plain password directly
        user = new User({
            name,
            email,
            mobile,
            location,
            password: password.trim(), // WARNING: Plain text password storage
        });

        await user.save();

        sendRegistrationEmail(email, name);

        res.status(201).json({ message: "✅ Registration successful! Please login." });
    } catch (error) {
        console.error("❌ Registration Error:", error);
        res.status(500).json({ message: "❌ Server error", error });
    }
});

/**
 * @route POST /api/auth/login
 * @desc  Authenticate user & get token
 * @access Public
 */
router.post("/login", async (req, res) => {
    try {
        const { email, password } = req.body;

        let user = await User.findOne({ email });
        if (!user) {
            return res.status(400).json({ message: "❌ Invalid email or password" });
        }

        console.log("🔑 Stored Password (Plain Text):", user.password); // Debugging log
        console.log("🔍 Entered Password:", password.trim()); // Debugging log

        // Directly compare passwords
        const isMatch = password.trim() === user.password;

        console.log("🔍 Password Match Result:", isMatch); // Debugging log

        if (!isMatch) {
            return res.status(400).json({ message: "❌ Invalid email or password" });
        }

        // Generate JWT token
        const token = jwt.sign({ id: user.id }, jwtSecret, { expiresIn: "1h" });

        res.status(200).json({ message: "✅ Login successful", token, userId: user.id });
    } catch (error) {
        console.error("❌ Login Error:", error);
        res.status(500).json({ message: "❌ Server error", error });
    }
});

module.exports = router;
