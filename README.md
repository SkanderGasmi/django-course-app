# 🎓 Online Course Platform

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Django](https://img.shields.io/badge/Django-3.2%2B-green.svg)
![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Tests](https://img.shields.io/badge/Tests-Comprehensive-brightgreen.svg)
![Architecture](https://img.shields.io/badge/Architecture-DDD%20%7C%20SOLID%20%7C%20TDD-blueviolet.svg)

A comprehensive Django-based learning management system with advanced assessment capabilities, built with enterprise-grade architecture and best practices.

---

## 📋 Overview

This platform provides a complete solution for online education, enabling instructors to create courses, lessons, and assessments while allowing learners to enroll, complete exams, and track their progress. The system features a robust assessment engine with automatic grading and detailed performance analytics.

---

## 🏗 Architecture

### Project Structure

```

onlinecourse/
├── admin/                  # Modular admin configuration
│   ├── base.py             # Reusable mixins and base classes
│   ├── course.py           # Course management interface
│   ├── lesson.py           # Lesson management interface
│   ├── question.py         # Assessment management interface
│   ├── enrollment.py       # Enrollment management interface
│   ├── submission.py       # Exam review interface
│   ├── learner.py          # Learner profile management
│   └── instructor.py       # Instructor profile management
│
├── models/                 # Domain-driven model design
│   ├── base.py             # Abstract base classes (TimeStampedModel)
│   ├── user_profiles.py    # Instructor and Learner models
│   ├── course.py           # Course model with denormalized fields
│   ├── lesson.py           # Ordered lesson content
│   ├── enrollment.py       # User-course relationship with metadata
│   ├── assessment.py       # Question and Choice with grading logic
│   └── submission.py       # Exam submissions and scoring
│
├── templates/              # Frontend templates
├── static/                 # Static assets (CSS, JS, images)
├── tests/                  # Comprehensive test suite
└── views.py                # Application views

````

---

## ✨ Key Features

### 🎓 For Learners

- **Course Enrollment**: Browse and enroll in available courses  
- **Interactive Assessments**: Take exams with multiple question types  
- **Instant Grading**: Receive immediate feedback on exam performance  
- **Progress Tracking**: Monitor completion status and scores  
- **Personal Dashboard**: View enrolled courses and achievements  

### 👨‍🏫 For Instructors

- **Course Management**: Create and organize course content  
- **Lesson Builder**: Structure learning materials with video integration  
- **Assessment Designer**: Build questions with multiple correct answers  
- **Grade Analytics**: View class performance and question difficulty metrics  
- **Student Insights**: Track individual learner progress  

### 🛠 For Administrators

- **Comprehensive Admin Interface**: Full CRUD operations for all models  
- **CSV Export**: Bulk export of submissions and enrollment data  
- **Performance Dashboard**: Visual indicators for scores and completion  
- **Audit Trail**: Automatic timestamp tracking for all records  
- **Permission Controls**: Role-based access (Instructor vs Superuser)  

---

## 💾 Data Model

### Core Entities

```python
Course              # Educational course container
├── Lesson          # Individual content units
├── Question        # Assessment items with point values
│   └── Choice      # Answer options with correctness flags
└── Enrollment      # User-course relationship
    └── Submission  # Exam attempts with selected answers
````

---

### Key Design Decisions

#### Denormalization for Performance

* `Course.total_enrollment`: Cached count of enrolled students
* `Course.average_rating`: Pre-calculated from enrollment ratings
* Eliminates expensive `COUNT(*)` and `AVG()` queries on large datasets

#### Database Indexing Strategy

```python
indexes = [
    models.Index(fields=['pub_date']),        # Course publication queries
    models.Index(fields=['course', 'order']), # Lesson ordering
    models.Index(fields=['user', 'course']),  # Enrollment lookups
]
```

#### Strict Grading Algorithm

* Questions can have multiple correct answers
* Full points awarded only when **ALL** correct choices are selected
* No partial credit (configurable for future enhancement)

---

## 🚀 Installation & Setup

### Prerequisites

* Python 3.8+
* Django 3.2+
* Virtual environment (recommended)

---

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd onlinecourse-platform

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata sample_courses.json

# Start development server
python manage.py runserver
```

---

### Environment Variables

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
```

---

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific test modules
python manage.py test onlinecourse.tests.test_models
python manage.py test onlinecourse.tests.test_views
python manage.py test onlinecourse.tests.test_admin

# Run with coverage report
coverage run --source='.' manage.py test
coverage report
```

---

## 📊 Performance Optimizations

1. **Query Optimization**

   * `select_related()` for ForeignKey relationships
   * `prefetch_related()` for ManyToMany and reverse relations
   * Custom queryset methods for common lookups

2. **Caching Strategy**

   * Denormalized counters for enrollment statistics
   * Template fragment caching for course listings
   * Database indexes on frequently filtered fields

3. **Pagination**

   * Admin list views: 50 items per page
   * Course listings: 12 items per page
   * API endpoints: Configurable page sizes

---

## 🔒 Security Features

* **CSRF Protection**: Enabled on all forms
* **XSS Prevention**: Django template auto-escaping
* **SQL Injection Protection**: Parameterized queries via ORM
* **Authentication**: Django's built-in auth system
* **Authorization**: Role-based permission checks
* **HTTPS Enforcement**: Configurable in production

---

## 📈 Monitoring & Analytics

Built-in metrics for:

* Course popularity (enrollment counts)
* Question difficulty (success rate per question)
* Student performance (score distributions)
* Instructor effectiveness (average ratings)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m "Add some amazing feature"`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

### Coding Standards

* Follow PEP 8 style guide
* Include docstrings for all classes and methods
* Write tests for new features
* Update documentation as needed

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

* Django Software Foundation for the framework
* All contributors who have helped shape this project

---

## 🧱 Built With

Django • Python • SQLite/PostgreSQL • Bootstrap • jQuery

**Architecture Principles:** Domain-Driven Design • SOLID • DRY • Test-Driven Development

---

*This project demonstrates enterprise-grade Django development practices including modular architecture, comprehensive testing, performance optimization, and detailed documentation.*

```
```
