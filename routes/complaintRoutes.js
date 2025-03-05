const express = require("express");
const Complaint = require("../models/Complaint");
const authMiddleware = require("../middleware/auth");

const router = express.Router();

/**
 * @route POST /api/complaints
 * @desc  Register a lost person complaint
 * @access Private (User must be logged in)
 */
router.post("/", authMiddleware, async (req, res) => {
    try {
        const { name, age, gender, lastSeenLocation, dateMissing, contactNumber, description, image } = req.body;

        // Validate required fields
        if (!name || !age || !gender || !lastSeenLocation || !dateMissing || !contactNumber || !description) {
            return res.status(400).json({ message: "All fields except image are required" });
        }

        const newComplaint = new Complaint({
            name,
            age,
            gender,
            lastSeenLocation,
            dateMissing,
            contactNumber,
            description,
            image,  // Base64 image stored as a string
            user: req.user.id,  // Capturing logged-in user ID
        });

        await newComplaint.save();
        res.status(201).json({ message: "Complaint registered successfully", complaint: newComplaint });

    } catch (error) {
        console.error("Error in complaint registration:", error);
        res.status(500).json({ message: "Server error", error: error.message });
    }
});

/**
 * @route GET /api/complaints
 * @desc  Get all registered complaints
 * @access Public
 */
router.get("/", async (req, res) => {
    try {
        const complaints = await Complaint.find().sort({ createdAt: -1 });
        res.status(200).json(complaints);
    } catch (error) {
        res.status(500).json({ message: "Server error", error });
    }
});

/**
 * @route GET /api/complaints/:id
 * @desc  Get a single complaint by ID
 * @access Public
 */
router.get("/:id", async (req, res) => {
    try {
        const complaint = await Complaint.findById(req.params.id);
        if (!complaint) return res.status(404).json({ message: "Complaint not found" });
        res.status(200).json(complaint);
    } catch (error) {
        res.status(500).json({ message: "Server error", error });
    }
});

/**
 * @route DELETE /api/complaints/:id
 * @desc  Delete a complaint (Only the user who created it can delete)
 * @access Private
 */
router.delete("/:id", authMiddleware, async (req, res) => {
    try {
        const complaint = await Complaint.findById(req.params.id);
        if (!complaint) return res.status(404).json({ message: "Complaint not found" });

        if (complaint.user.toString() !== req.user.id) {
            return res.status(403).json({ message: "Unauthorized to delete this complaint" });
        }

        await complaint.deleteOne();
        res.status(200).json({ message: "Complaint deleted successfully" });
    } catch (error) {
        res.status(500).json({ message: "Server error", error });
    }
});

module.exports = router;
