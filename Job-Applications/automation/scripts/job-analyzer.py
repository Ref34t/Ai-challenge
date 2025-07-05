#!/usr/bin/env python3
"""
Upwork Job Analyzer
Processes job posts and extracts market intelligence
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class JobPost:
    """Structure for individual job post analysis"""
    job_id: str
    title: str
    budget: str
    timeline: str
    skills_required: List[str]
    client_location: str
    client_history: str
    proposals: int
    description: str
    opportunity_score: int
    category: str
    subcategory: str
    notes: str = ""

class UpworkJobAnalyzer:
    """Main analyzer class for processing job posts"""
    
    def __init__(self):
        self.skill_keywords = {
            'web_development': {
                'frontend': ['react', 'vue', 'angular', 'javascript', 'typescript', 'html', 'css'],
                'backend': ['node', 'python', 'php', 'laravel', 'django', 'express'],
                'fullstack': ['full-stack', 'fullstack', 'mern', 'mean', 'lamp'],
                'wordpress': ['wordpress', 'wp', 'elementor', 'gutenberg', 'woocommerce']
            },
            'mobile_apps': {
                'ios': ['ios', 'swift', 'objective-c', 'xcode'],
                'android': ['android', 'kotlin', 'java', 'android studio'],
                'react_native': ['react native', 'expo'],
                'flutter': ['flutter', 'dart']
            },
            'ai_ml': {
                'chatbots': ['chatbot', 'bot', 'conversational ai', 'dialogue'],
                'automation': ['automation', 'scraping', 'workflow', 'zapier'],
                'data_analysis': ['data analysis', 'pandas', 'numpy', 'visualization'],
                'machine_learning': ['machine learning', 'ai', 'tensorflow', 'pytorch']
            },
            'design': {
                'ui_ux': ['ui', 'ux', 'user experience', 'user interface'],
                'graphic_design': ['logo', 'branding', 'graphic design', 'photoshop'],
                'branding': ['brand identity', 'brand design', 'corporate identity'],
                'figma': ['figma', 'sketch', 'adobe xd']
            }
        }
        
        self.budget_ranges = {
            'micro': (0, 50),
            'small': (50, 500),
            'medium': (500, 5000),
            'large': (5000, float('inf'))
        }
    
    def extract_skills(self, description: str, title: str) -> List[str]:
        """Extract skills from job description and title"""
        text = (description + " " + title).lower()
        found_skills = []
        
        for category, subcategories in self.skill_keywords.items():
            for subcategory, keywords in subcategories.items():
                for keyword in keywords:
                    if keyword in text:
                        found_skills.append(keyword)
        
        return list(set(found_skills))
    
    def categorize_job(self, skills: List[str], title: str, description: str) -> tuple:
        """Categorize job based on skills and content"""
        text = (title + " " + description).lower()
        
        # Score each category
        category_scores = {}
        for category, subcategories in self.skill_keywords.items():
            category_scores[category] = 0
            for subcategory, keywords in subcategories.items():
                for keyword in keywords:
                    if keyword in text:
                        category_scores[category] += 1
        
        # Get highest scoring category
        main_category = max(category_scores, key=category_scores.get)
        
        # Find subcategory
        subcategory_scores = {}
        for subcategory, keywords in self.skill_keywords[main_category].items():
            subcategory_scores[subcategory] = 0
            for keyword in keywords:
                if keyword in text:
                    subcategory_scores[subcategory] += 1
        
        subcategory = max(subcategory_scores, key=subcategory_scores.get)
        
        return main_category, subcategory
    
    def extract_budget(self, budget_text: str) -> str:
        """Extract and categorize budget information"""
        if not budget_text:
            return "unknown"
        
        # Extract numbers from budget text
        numbers = re.findall(r'\d+', budget_text.replace(',', ''))
        if not numbers:
            return "unknown"
        
        # Take the highest number found
        max_budget = max(int(num) for num in numbers)
        
        for range_name, (min_val, max_val) in self.budget_ranges.items():
            if min_val <= max_budget < max_val:
                return range_name
        
        return "large"
    
    def calculate_opportunity_score(self, job: JobPost) -> int:
        """Calculate opportunity score based on various factors"""
        score = 5  # Base score
        
        # Budget factor (higher budget = higher score)
        budget_bonus = {
            'micro': 0, 'small': 2, 'medium': 4, 'large': 6
        }
        score += budget_bonus.get(job.budget, 0)
        
        # Competition factor (lower competition = higher score)
        if job.proposals < 10:
            score += 3
        elif job.proposals < 25:
            score += 1
        elif job.proposals > 50:
            score -= 2
        
        # Skill match factor (more relevant skills = higher score)
        if len(job.skills_required) > 0:
            score += min(len(job.skills_required), 3)
        
        # Client history factor
        if 'established' in job.client_history.lower():
            score += 1
        
        return min(max(score, 1), 10)  # Keep between 1-10
    
    def process_job_post(self, job_data: Dict[str, Any]) -> JobPost:
        """Process a single job post and return structured data"""
        
        # Extract skills
        skills = self.extract_skills(
            job_data.get('description', ''),
            job_data.get('title', '')
        )
        
        # Categorize
        category, subcategory = self.categorize_job(
            skills,
            job_data.get('title', ''),
            job_data.get('description', '')
        )
        
        # Create job post object
        job = JobPost(
            job_id=job_data.get('id', ''),
            title=job_data.get('title', ''),
            budget=self.extract_budget(job_data.get('budget', '')),
            timeline=job_data.get('timeline', ''),
            skills_required=skills,
            client_location=job_data.get('client_location', ''),
            client_history=job_data.get('client_history', ''),
            proposals=int(job_data.get('proposals', 0)),
            description=job_data.get('description', ''),
            opportunity_score=0,  # Will be calculated
            category=category,
            subcategory=subcategory,
            notes=job_data.get('notes', '')
        )
        
        # Calculate opportunity score
        job.opportunity_score = self.calculate_opportunity_score(job)
        
        return job
    
    def analyze_batch(self, job_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a batch of job posts"""
        processed_jobs = []
        
        for job_data in job_posts:
            try:
                job = self.process_job_post(job_data)
                processed_jobs.append(job)
            except Exception as e:
                print(f"Error processing job {job_data.get('id', 'unknown')}: {e}")
        
        # Generate analysis
        analysis = {
            'total_jobs': len(processed_jobs),
            'categories': self._analyze_categories(processed_jobs),
            'budgets': self._analyze_budgets(processed_jobs),
            'competition': self._analyze_competition(processed_jobs),
            'top_skills': self._analyze_skills(processed_jobs),
            'opportunities': self._find_opportunities(processed_jobs),
            'processed_jobs': [asdict(job) for job in processed_jobs]
        }
        
        return analysis
    
    def _analyze_categories(self, jobs: List[JobPost]) -> Dict[str, int]:
        """Analyze job categories"""
        categories = {}
        for job in jobs:
            key = f"{job.category}.{job.subcategory}"
            categories[key] = categories.get(key, 0) + 1
        return categories
    
    def _analyze_budgets(self, jobs: List[JobPost]) -> Dict[str, int]:
        """Analyze budget distribution"""
        budgets = {}
        for job in jobs:
            budgets[job.budget] = budgets.get(job.budget, 0) + 1
        return budgets
    
    def _analyze_competition(self, jobs: List[JobPost]) -> Dict[str, Any]:
        """Analyze competition levels"""
        competitions = {'low': 0, 'medium': 0, 'high': 0}
        total_proposals = 0
        
        for job in jobs:
            total_proposals += job.proposals
            if job.proposals < 10:
                competitions['low'] += 1
            elif job.proposals < 25:
                competitions['medium'] += 1
            else:
                competitions['high'] += 1
        
        return {
            'distribution': competitions,
            'average_proposals': total_proposals / len(jobs) if jobs else 0
        }
    
    def _analyze_skills(self, jobs: List[JobPost]) -> Dict[str, int]:
        """Analyze most requested skills"""
        skills = {}
        for job in jobs:
            for skill in job.skills_required:
                skills[skill] = skills.get(skill, 0) + 1
        
        # Return top 10 skills
        return dict(sorted(skills.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def _find_opportunities(self, jobs: List[JobPost]) -> List[Dict[str, Any]]:
        """Find high-opportunity jobs"""
        opportunities = []
        
        for job in jobs:
            if job.opportunity_score >= 7:
                opportunities.append({
                    'job_id': job.job_id,
                    'title': job.title,
                    'score': job.opportunity_score,
                    'budget': job.budget,
                    'proposals': job.proposals,
                    'category': f"{job.category}.{job.subcategory}"
                })
        
        return sorted(opportunities, key=lambda x: x['score'], reverse=True)

def main():
    """Main function for command-line usage"""
    analyzer = UpworkJobAnalyzer()
    
    # Example usage
    sample_jobs = [
        {
            'id': 'sample1',
            'title': 'React Developer Needed',
            'description': 'Looking for a React developer to build a modern web application',
            'budget': '$500-1000',
            'timeline': '2 weeks',
            'client_location': 'USA',
            'client_history': 'Established client',
            'proposals': 15
        }
    ]
    
    results = analyzer.analyze_batch(sample_jobs)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()