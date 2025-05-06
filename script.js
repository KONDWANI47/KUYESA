// Mock music database for search
const musicDatabase = [
  { title: "Story Telling Beat", artist: "Cupicsart", genre: "Trap" },
  { title: "Africa Trap", artist: "Cupicsart", genre: "Trap" },
  { title: "SUDZIWA", artist: "Phyzix ft Quest", genre: "Hip Hop" },
  { title: "WADONGO", artist: "Jay Jay ft MAN-CHI", genre: "Hip Hop" },
  { title: "MISOZI", artist: "Waxy Kay", genre: "R&B" },
  { title: "ADZALIRA", artist: "Carbon MW", genre: "Hip Hop" },
  { title: "Jaguar Paw Volume I", artist: "Jaguar", genre: "Afro" },
]

// DOM Elements
const searchBtn = document.querySelector(".search-btn")
const searchInput = document.getElementById("search-input")
const searchResults = document.getElementById("search-results")
const resultsList = document.getElementById("results-list")
const messagesDiv = document.getElementById("messages")
const hamburgerBtn = document.querySelector(".hamburger")
const navLinks = document.querySelector(".nav-links")

// Utility to show messages
const showMessage = (message, type = "success") => {
  messagesDiv.innerHTML = `<p class="${type}">${message}</p>`
  messagesDiv.focus()
  setTimeout(() => (messagesDiv.innerHTML = ""), 5000)
}

// Utility to clear errors
const clearErrors = (form) => {
  if (!form) return
  const errorElements = form.querySelectorAll(".error")
  errorElements.forEach((span) => (span.textContent = ""))
}

// Validate email
const validateEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

// Hamburger menu toggle
if (hamburgerBtn) {
  hamburgerBtn.addEventListener("click", () => {
    const expanded = hamburgerBtn.getAttribute("aria-expanded") === "true"
    hamburgerBtn.setAttribute("aria-expanded", !expanded)
    navLinks.classList.toggle("active")
  })
}

// Search functionality
if (searchBtn && searchInput) {
  searchBtn.addEventListener("click", performSearch)
  searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      performSearch()
    }
  })
}

function performSearch() {
  const query = searchInput.value.trim().toLowerCase()
  resultsList.innerHTML = ""

  if (!query) {
    showMessage("Please enter a search term", "error")
    searchResults.classList.remove("active")
    return
  }

  const results = musicDatabase.filter(
    (item) =>
      item.title.toLowerCase().includes(query) ||
      item.artist.toLowerCase().includes(query) ||
      item.genre.toLowerCase().includes(query),
  )

  searchResults.classList.add("active")

  if (results.length === 0) {
    resultsList.innerHTML = "<li>No results found</li>"
    return
  }

  results.forEach((item) => {
    const li = document.createElement("li")
    li.textContent = `${item.title} by ${item.artist} (${item.genre})`
    resultsList.appendChild(li)
  })
}

// Form submission handler
const handleFormSubmit = (formId, validate, mockApi) => {
  const form = document.getElementById(formId)
  if (!form) return

  form.addEventListener("submit", async (e) => {
    e.preventDefault()
    clearErrors(form)

    const formData = new FormData(form)
    const data = Object.fromEntries(formData)
    const errors = validate(data)

    if (Object.keys(errors).length > 0) {
      Object.entries(errors).forEach(([key, message]) => {
        const errorElement = form.querySelector(`.error.${key}`)
        if (errorElement) {
          errorElement.textContent = message
        }
      })
      return
    }

    try {
      // Simulate API call
      const response = await mockApi(data)
      showMessage(response.message)
      form.reset()
    } catch (error) {
      showMessage(error.message || "An error occurred", "error")
    }
  })
}

// Contact form
handleFormSubmit(
  "contact-form",
  (data) => {
    const errors = {}
    if (!data["contact-name"] || data["contact-name"].length < 2) {
      errors.name = "Name must be at least 2 characters"
    }
    if (!data["contact-email"] || !validateEmail(data["contact-email"])) {
      errors.email = "Invalid email"
    }
    if (!data["contact-message"] || data["contact-message"].length < 10) {
      errors.message = "Message must be at least 10 characters"
    }
    return errors
  },
  async () => {
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1000))
    return { message: "Message sent successfully! We'll get back to you soon." }
  },
)

// Audio upload form
handleFormSubmit(
  "upload-form",
  (data) => {
    const errors = {}
    if (!data["audio-title"] || data["audio-title"].length < 3) {
      errors.title = "Title must be at least 3 characters"
    }

    const fileInput = document.getElementById("audio-file")
    if (fileInput) {
      const file = fileInput.files[0]
      if (!file) {
        errors.file = "Please select an audio file"
      } else {
        const validTypes = ["audio/mp3", "audio/mpeg", "audio/wav"]
        if (!validTypes.includes(file.type)) {
          errors.file = "Only MP3 or WAV files are allowed"
        }
        if (file.size > 10 * 1024 * 1024) {
          errors.file = "File size must be less than 10MB"
        }
      }
    }
    return errors
  },
  async () => {
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 1500))
    return { message: "Audio uploaded successfully!" }
  },
)

// Initialize page-specific functionality
document.addEventListener("DOMContentLoaded", () => {
  // Close search results when clicking outside
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-bar") && !e.target.closest(".search-results")) {
      searchResults.classList.remove("active")
    }
  })
})
