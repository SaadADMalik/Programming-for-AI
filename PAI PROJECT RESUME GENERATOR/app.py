from flask import Flask, render_template, request, send_file
from weasyprint import HTML
from io import BytesIO
import re
import os
import requests

app = Flask(__name__)

# Groq API setup (requires GROQ_API_KEY environment variable)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print(f"Using GROQ_API_KEY: {GROQ_API_KEY}")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set. Please set it before running the app.")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_resume():
    try:
        # Server-side validation
        name = request.form['name'].strip()
        contact = request.form['contact'].strip()
        education = request.form['education'].strip().replace(r'$\mathrm{Al}$', 'AI').replace('[Name of University]', '').replace('[Graduation Date]', '')
        experience = request.form['experience'].strip()
        skills = request.form['skills'].strip()

        if not all([name, contact, education, experience, skills]):
            return "All fields are required", 400

        # Clean and split experience and skills
        exp_lines = [line.strip() for line in experience.split('\n') if line.strip()]
        skill_lines = [re.sub(r'^\.\s*\.\s*', '', line.strip()) for line in skills.split('\n') if line.strip()]

        # Create a highly directive prompt for Groq API
        prompt = f"Generate a professional resume for a data analyst role. Rewrite every section with enhanced clarity, professionalism, and impact. Add quantifiable achievements (e.g., 15% improvement, 2 years) even if not in the input. Do not reproduce input verbatim; rephrase all content. Use these details:\n- Name: {name}\n- Contact: {contact}\n- Education: {education}\n- Experience: {experience}\n- Skills: {skills}\n"
        prompt += "Structure the resume as:\n- Summary: A compelling overview of skills and achievements.\n- Experience: Rewrite each job entry and bullet point with professional language and added value (e.g., metrics, outcomes).\n- Education: Provide the degree and institution (omit placeholders).\n- Skills: Rewrite all skills into professional bullet points, ensuring all input skills are included and relevant to data analysis.\nEnsure the output is complete, with no missing sections or truncated content."

        # Call Groq API with updated model
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "llama-3.3-70b-versatile",  # Updated to a supported model
            "max_tokens": 6000
        }
        response = requests.post(GROQ_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Groq API request failed: {response.status_code} - {response.text}")
        response.raise_for_status()

        generated_text = response.json()['choices'][0]['message']['content']

        # Post-process the generated content to extract sections
        sections = {
            "Summary": "",
            "Experience": [],
            "Education": "",
            "Skills": []
        }

        current_section = None
        for line in generated_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            if "Summary" in line:
                current_section = "Summary"
                continue
            elif "Experience" in line:
                current_section = "Experience"
                continue
            elif "Education" in line:
                current_section = "Education"
                continue
            elif "Skills" in line:
                current_section = "Skills"
                continue

            if current_section == "Summary":
                sections["Summary"] += line + " "
            elif current_section == "Experience" and line.startswith('-'):
                sections["Experience"].append(line[1:].strip())
            elif current_section == "Education":
                sections["Education"] += line + " "
            elif current_section == "Skills" and line.startswith('-'):
                sections["Skills"].append(line[1:].strip())

        # Fallback and enhancement if sections are incomplete
        if not sections["Summary"]:
            sections["Summary"] = f"Dynamic Data Analyst with a proven track record in leveraging AI and advanced analytics to optimize business performance."
        if not sections["Experience"] or len(sections["Experience"]) < len(exp_lines):
            sections["Experience"] = [
                f"Transformed data analysis processes, achieving a 15% efficiency gain" if "Monitored" in exp else
                f"Designed automated Power BI dashboards, improving decision-making by 20%" if "Developed" in exp else
                f"Streamlined data workflows with Python and SQL, reducing processing time by 40%" if "Integrated" in exp else
                f"Delivered client-focused insights, boosting retention by 30%" if "Collaborated" in exp else exp
                for exp in exp_lines
            ]
        if not sections["Education"]:
            sections["Education"] = education
        if not sections["Skills"] or len(sections["Skills"]) < len(skill_lines):
            sections["Skills"] = [
                f"Expertise in Data Analysis & Reporting with Advanced Excel, SQL, Python (Pandas, NumPy), and Power BI" if "Data Analysis" in skill else
                f"Proficient in Performance Monitoring via KPI tracking, trend analysis, and anomaly detection" if "Performance Monitoring" in skill else
                f"Skilled in Data Visualization using Power BI dashboards" if "Data Visualization" in skill else
                f"Competent in Database Management with SQL, SQLite, MySQL, and data integration" if "Database Management" in skill else
                f"Strong Professional Skills including communication, time management, and collaboration" if "Professional Skills" in skill else skill
                for skill in skill_lines
            ]

        # Post-process to fix formatting (remove $ from percentages)
        sections["Experience"] = [re.sub(r'\$(\d+%)\b', r'\1', item) for item in sections["Experience"]]
        sections["Skills"] = [re.sub(r'\$(\d+%)\b', r'\1', item) for item in sections["Skills"]]

        # Remove irrelevant content
        sections["Experience"] = [item for item in sections["Experience"] if not re.search(r'salary|income|benefits|intelligent analytics|talwar', item, re.IGNORECASE)]
        sections["Skills"] = [item for item in sections["Skills"] if not re.search(r'salary|income|benefits|intelligent analytics|talwar|professions|career advancement', item, re.IGNORECASE)]

        # Format sections into HTML
        experience_items = [f"<li>{item}</li>" for item in sections["Experience"]]
        skills_items = [f"<li>{item}</li>" for item in sections["Skills"]]

        # HTML structure for the PDF with embedded CSS
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 30px; }}
                h1 {{ text-align: center; color: #333; margin-bottom: 10px; }}
                .contact {{ text-align: center; margin-bottom: 20px; color: #555; }}
                h2 {{ color: #444; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 20px; margin-bottom: 10px; }}
                ul {{ margin: 10px 0; padding-left: 20px; list-style-type: disc; }}
                li {{ margin-bottom: 5px; line-height: 1.5; }}
                p {{ margin: 5px 0; line-height: 1.5; }}
                a {{ color: #007bff; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>{name}</h1>
            <div class="contact">
                <p><a href="mailto:{contact}">{contact}</a></p>
            </div>

            <h2>Summary</h2>
            <p>{sections['Summary'].strip()}</p>

            <h2>Experience</h2>
            <ul>
                {''.join(experience_items)}
            </ul>

            <h2>Education</h2>
            <p>{sections['Education'].strip()}</p>

            <h2>Skills</h2>
            <ul>
                {''.join(skills_items)}
            </ul>
        </body>
        </html>
        """
        
        # Generate the PDF
        pdf = HTML(string=html).write_pdf()
        pdf_file = BytesIO(pdf)
        
        # Send the PDF as a response
        return send_file(pdf_file, as_attachment=True, download_name='resume.pdf', mimetype='application/pdf')
    except Exception as e:
        return f"Error generating resume: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=False)