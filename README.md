<div align="center">

<img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white"/>
<img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Gemini_AI-Powered-4285F4?style=for-the-badge&logo=google&logoColor=white"/>
<img src="https://img.shields.io/badge/Tailwind_CSS-3.x-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white"/>

# 🏠 NestMatch

### _Find Your Perfect Match, Not Just a Room._

**NestMatch** is a smart, AI-powered roommate and room-rental matching platform.
It uses **Google Gemini AI** to score compatibility between people based on real lifestyle data —
sleep schedule, cleanliness, noise level, smoking habits, pets, and more.

</div>

---

## Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Pages](#pages)
- [Getting Started](#getting-started)
- [Team](#team)

---

## About the Project

This is the **Graduation Final Project** for the Full-Stack Web Development program at **AXSOS Academy — 2026**.

NestMatch was designed to solve a real problem: finding compatible roommates is hard.
Traditional platforms match people by location and price alone. NestMatch goes further —
it builds a **lifestyle profile** for every user and uses AI to compute a real compatibility
score before a single message is sent.

---

## Features

| Feature                      | Description                                                                                        |
| ---------------------------- | -------------------------------------------------------------------------------------------------- |
| **AI Compatibility Scoring** | Gemini API compares lifestyle profiles and returns a 0–100% match with factor-by-factor breakdown  |
| **Lifestyle Questionnaire**  | 6-step wizard after registration — sleep, noise, cleanliness, smoking, pets, background            |
| **Smart Search & Filters**   | Filter by price, location, listing type, gender preference, smoking, pets, and min compatibility % |
| **Interactive Map**          | Google Maps with custom pins, popup previews, and distance filter                                  |
| **AI Room Descriptions**     | Click one button — Gemini writes a professional listing description instantly                      |
| **AI Rental Agreements**     | Gemini drafts a full rental contract, downloadable as a PDF                                        |
| **Instant WhatsApp Contact** | One-click WhatsApp link on every listing                                                           |
| **Applicant Management**     | Posters review applicants sorted by compatibility score, accept/reject with AJAX                   |
| **Admin Panel**              | Full custom dashboard — user management, banning, listing moderation, platform stats               |
| **Fully Responsive**         | Mobile-first design with Tailwind CSS                                                              |

---

## Tech Stack

| Layer              | Technology                        |
| ------------------ | --------------------------------- |
| **Backend**        | Django 6.0 · Python 3.13          |
| **Database**       | SQLite (development)              |
| **Frontend**       | Tailwind CSS · Vanilla JavaScript |
| **AI**             | Google Gemini API                 |
| **Maps**           | Google Maps JavaScript API        |
| **Authentication** | Django Auth · Google OAuth        |
| **PDF Generation** | WeasyPrint                        |
| **Messaging**      | WhatsApp API (`wa.me` links)      |

---

## Project Structure

```
NestMatchProject/
│
├── manage.py
├── requirements.txt
├── .gitignore
├── README.md
│
├── nest_match_project/          # Project settings, root URLs, wsgi, asgi
│
├── core_app/                    # Landing page · About · 404 / 500
├── accounts_app/                # Auth · Registration · Questionnaire · Profile
├── listings_app/                # Room listings · Post a room · Search · Detail
├── compatibility_app/           # AI compatibility scoring (Gemini API)
├── applications_app/            # Apply · Accept · Reject
├── agreements_app/              # AI rental agreement · PDF download
└── dashboard_app/               # Poster dashboard · Seeker tracker · Admin panel
```

---

## Pages

| #   | URL                        | Page                                                |
| --- | -------------------------- | --------------------------------------------------- |
| 1   | `/`                        | Landing page                                        |
| 2   | `/auth/`                   | Login / Register                                    |
| 3   | `/questionnaire/`          | 6-step lifestyle questionnaire                      |
| 4   | `/rooms/`                  | Room listings with live AJAX filters + map          |
| 5   | `/rooms/<id>/`             | Room detail + AI compatibility breakdown            |
| 6   | `/rooms/new/`              | Post a room — 4-step form + AI description          |
| 7   | `/dashboard/`              | Poster dashboard — listings, applicants, agreements |
| 8   | `/dashboard/applications/` | Seeker — track all applications by status           |
| 9   | `/profile/`                | Profile — personal info, lifestyle, security        |
| 10  | `/admin-panel/`            | Custom admin panel                                  |

---

## Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/your-username/nestmatch.git
cd nestmatch

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
python manage.py migrate

# 5. Create a superuser
python manage.py createsuperuser

# 6. Run the server
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.


## Output
### Register Page
![Register Page](docs/screenshots/Register.png)

<br>

### Login Page
![Login Page](docs/screenshots/Login.png)

<br>

### Landing Page
![Landing Page](docs/screenshots/Landing.png)

<br>

### Frequently Asked Questions Page
![Frequently Asked Questions Page](docs/screenshots/Faq.png)

<br>

### Contact Us Page
![Contact Us Page](docs/screenshots/Contact.png)

<br>

### Rooms Page
![Rooms Page](docs/screenshots/Rooms.png)

<br>

### Post Room Steps
![Basic Information](docs/screenshots/post-step1.png)
![Location](docs/screenshots/post-step2.png)
![Photos](docs/screenshots/post-step3.png)
![Requirements](docs/screenshots/post-step4.png)
![Review](docs/screenshots/post-step5.png)

<br>

### Profile Page
![Profile Page](docs/screenshots/profile.png)

<br>

### My Room Page
![My Room Page](<docs/screenshots/My%20Room.jpeg>)

<br>

### Favorite Page
![Favorite Page](docs/screenshots/Favorite.jpeg)

<br>

### Applications Page
![Applications Page](docs/screenshots/Applications.jpeg)

<br>

### Admin dashboard Page
![Admin dashboard Page](docs/screenshots/Admin.png)
---

## Team

AXSOS Academy — Graduation Final Project, 2026

- **Mostafa Aljazar** — Team Lead · [@Mostafa-Aljazar](https://github.com/Mostafa-Aljazar)
- **Amira Jarghon** — [@AmiraAliJa1282001](https://github.com/AmiraAliJa1282001)
- **Noor Shurrab** — [@NoorShurrab](https://github.com/NoorShurrab)
- **Sara Ayyash** — [@Sara-ayyash1](https://github.com/Sara-ayyash1)

---

<div align="center">Made with ❤️ by the NestMatch Team · AXSOS Academy · 2026</div>
