"""

    cv_generator_overleaf.py

    Author: Mohamed Elgazar 

    Description:
    This script generates a CV in LaTeX format using the provided data and styles.

    Usage:
    1. Change the data in the variables below and run the script.
    2. Run the script using python cv_generator_overleaf.py

    Output:
    A CV in LaTeX format.

"""

import os
import json
from datetime import datetime

class Generator:

    source_path = ""
    cv_data = {}
    cv_str = ""

    def __init__(self, source_path):
        self.source_path = source_path
        self.extract_cv_info()
        

    def extract_cv_info(self):
        with open(self.source_path, "r") as file:
            self.cv_data = json.load(file)
    
    def add_header(self):
        return r"""\documentclass[10pt, letterpaper]{article}
% Packages:
\usepackage[
    ignoreheadfoot, % set margins without considering header and footer
    top=2 cm, % separation between body and page edge from the top
    bottom=2 cm, % separation between body and page edge from the bottom
    left=2 cm, % separation between body and page edge from the left
    right=2 cm, % separation between body and page edge from the right
    footskip=1.0 cm, % separation between body and footer
    % showframe % for debugging 
]{geometry} % for adjusting page geometry
\usepackage{titlesec} % for customizing section titles
\usepackage{tabularx} % for making tables with fixed width columns
\usepackage{array} % tabularx requires this
\usepackage[dvipsnames]{xcolor} % for coloring text
\definecolor{primaryColor}{RGB}{0, 0, 0} % define primary color
\usepackage{enumitem} % for customizing lists
\usepackage{fontawesome5} % for using icons
\usepackage{amsmath} % for math
\usepackage[
    pdftitle={MG},
    pdfauthor={MG},
    pdfcreator={LaTeX with RenderCV},
    colorlinks=true,
    urlcolor=primaryColor
]{hyperref} % for links, metadata and bookmarks
\usepackage[pscoord]{eso-pic} % for floating text on the page
\usepackage{calc} % for calculating lengths
\usepackage{bookmark} % for bookmarks
\usepackage{lastpage} % for getting the total number of pages
\usepackage{changepage} % for one column entries (adjustwidth environment)
\usepackage{paracol} % for two and three column entries
\usepackage{ifthen} % for conditional statements
\usepackage{needspace} % for avoiding page break right after the section title
\usepackage{iftex} % check if engine is pdflatex, xetex or luatex

% Ensure that generated PDF is machine-readable/ATS parsable:
\ifPDFTeX
    \input{glyphtounicode}
    \pdfgentounicode=1
    \usepackage[T1]{fontenc}
    \usepackage[utf8]{inputenc}
    \usepackage{lmodern}
\fi

\usepackage{charter}

% Some settings:
\raggedright
\AtBeginEnvironment{adjustwidth}{\partopsep0pt} % remove space before adjustwidth environment
\pagestyle{empty} % no header or footer
\setcounter{secnumdepth}{0} % no section numbering
\setlength{\parindent}{0pt} % no indentation
\setlength{\topskip}{0pt} % no top skip
\setlength{\columnsep}{0.15cm} % set column separation
\pagenumbering{gobble} % no page numbering

\titleformat{\section}{\needspace{4\baselineskip}\bfseries\large}{}{0pt}{}[\vspace{1pt}\titlerule]

\titlespacing{\section}{
    % left space:
    -1pt
}{
    % top space:
    0.3 cm
}{
    % bottom space:
    0.2 cm
} % section title spacing

\renewcommand\labelitemi{$\vcenter{\hbox{\small$\bullet$}}$} % custom bullet points
\newenvironment{highlights}{
    \begin{itemize}[
        topsep=0.10 cm,
        parsep=0.10 cm,
        partopsep=0pt,
        itemsep=0pt,
        leftmargin=0 cm + 10pt
    ]
}{
    \end{itemize}
} % new environment for highlights

\newenvironment{highlightsforbulletentries}{
    \begin{itemize}[
        topsep=0.10 cm,
        parsep=0.10 cm,
        partopsep=0pt,
        itemsep=0pt,
        leftmargin=10pt
    ]
}{
    \end{itemize}
} % new environment for highlights for bullet entries

\newenvironment{onecolentry}{
    \begin{adjustwidth}{
        0 cm + 0.00001 cm
    }{
        0 cm + 0.00001 cm
    }
}{
    \end{adjustwidth}
} % new environment for one column entries

\newenvironment{twocolentry}[2][]{
    \onecolentry
    \def\secondColumn{#2}
    \setcolumnwidth{\fill, 4.5 cm}
    \begin{paracol}{2}
}{
    \switchcolumn \raggedleft \secondColumn
    \end{paracol}
    \endonecolentry
} % new environment for two column entries

\newenvironment{threecolentry}[3][]{
    \onecolentry
    \def\thirdColumn{#3}
    \setcolumnwidth{, \fill, 4.5 cm}
    \begin{paracol}{3}
    {\raggedright #2} \switchcolumn
}{
    \switchcolumn \raggedleft \thirdColumn
    \end{paracol}
    \endonecolentry
} % new environment for three column entries

\newenvironment{header}{
    \setlength{\topsep}{0pt}\par\kern\topsep\centering\linespread{1.5}
}{
    \par\kern\topsep
} % new environment for the header

\newcommand{\placelastupdatedtext}{% \placetextbox{<horizontal pos>}{<vertical pos>}{<stuff>}
  \AddToShipoutPictureFG*{% Add <stuff> to current page foreground
    \put(
        \LenToUnit{\paperwidth-2 cm-0 cm+0.05cm},
        \LenToUnit{\paperheight-1.0 cm}
    ){\vtop{{\null}\makebox[0pt][c]{
        \small\color{gray}\textit{Last updated in September 2024}\hspace{\widthof{Last updated in September 2024}}
    }}}%
  }%
}%

% save the original href command in a new command:
\let\hrefWithoutArrow\href

% new command for external links:

\newcommand{\mysspace}{0.1cm}
\newcommand{\mainsectionsspace}{0.3cm}
\newcommand{\MainHeaderSpace}{0.25cm}
\newcommand{\SecHeaderSpace}{0.15cm}
\newcommand{\SecAfterHeaderSpace}{0.25cm}

\usepackage{graphicx}
\usepackage{multicol}
\usepackage{enumitem}


\begin{document}
    \newcommand{\AND}{\unskip
        \cleaders\copy\ANDbox\hskip\wd\ANDbox
        \ignorespaces
    }
    \newsavebox\ANDbox
    \sbox\ANDbox{$|$}
    """

    def decode_date(self, date):
        # check if the date is "Present"
        if date == "Present":
            return "Present"
        try:
            # parse the date string
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            # convert to readable format like "Dec 2023"
            return date_obj.strftime("%b %Y")
        except ValueError as e:
            print(f"Error parsing date: {date} - {e}")
            return date  # Return the original value if parsing fails
         
    def generate_personl_info(self):
        # Get image path from JSON data
        image_path = self.cv_data["personal_info"].get("image_path", "N\\A")  # Default to image.png if not specified
        
        personal_info_str = (
            r"""
\noindent
\begin{minipage}[c]{0.22\textwidth}
    \centering
    \includegraphics[width=3.3cm,clip,trim=0 0 0 0]{"""
            + image_path
            + r"""}
\end{minipage}
\hfill
\begin{minipage}[c]{0.75\textwidth}
    \vspace*{0.3cm}
    \begin{flushleft}
        {\bfseries\LARGE """
            + self.cv_data["personal_info"]["name"]
            + r"""} \\[6pt]
        \href{mailto:"""
            + self.cv_data["personal_info"]["email"]
            + r"""}{"""
            + self.cv_data["personal_info"]["email"]
            + r"""} \\
        \vspace*{\mysspace}
        \href{tel:"""
            + self.cv_data["personal_info"]["phone"]
            + r"""}{"""
            + self.cv_data["personal_info"]["phone"]
            + r"""} \\
        \vspace*{\mysspace}
        """
            + self.cv_data["personal_info"]["location"]
            + r""" \\
        \vspace*{\mysspace}
        \href{"""
            + self.cv_data["personal_info"]["linkedin"]
            + r"""}{LinkedIn} /
        \vspace*{\mysspace}
        \href{"""
            + self.cv_data["personal_info"]["github"]
            + r"""}{Github} 
        \vspace*{\mysspace}
    \end{flushleft}
\end{minipage}
\vspace{\mainsectionsspace}
"""
        )
        return personal_info_str

    def generate_objective(self):
        objective_str = ""

        objective_str += r"""
    \section{Objective}
            \vspace{\MainHeaderSpace}
        \begin{onecolentry}
        """
        objective_str += self.cv_data["content"]["objective"]

        objective_str += r"""
        \end{onecolentry}
        \vspace{\mainsectionsspace}

    """

        return objective_str

    def generate_education(self):
        education_str = ""

        education_str += r"""
    \section{Education}
            \vspace{\MainHeaderSpace}

    """

        for s_education in self.cv_data["content"]["education"]:
            education_str += r"""
        \begin{twocolentry}{
            """
            education_str += (
                self.decode_date(s_education["startDate"])
                + " - "
                + self.decode_date(s_education["endDate"])
            )
            education_str += r"""
        }
            \textbf{"""
            education_str += s_education["university"]
            education_str += r"""}, """
            education_str += s_education["degree"]
            education_str += r"""
        \end{twocolentry}

        \vspace{\SecHeaderSpace}
        \begin{onecolentry}
            \begin{highlights}
                \item GPA: 
                """
            education_str += s_education["gpa"]

            if s_education["certificate"] != "N/A" and s_education["certificate"] != "N\\A":
                education_str += r"""(\href{"""
                education_str += s_education["certificate"]
                education_str += r"""}{Certificate})"""
                
            education_str += r"""
            \item \textbf{Coursework:} """
            education_str += s_education["coursework"]
            education_str += r"""
            \end{highlights}
        \end{onecolentry}
                \vspace{\SecAfterHeaderSpace}

        """

        return education_str

    def generate_short_education(self):
        short_education_str = ""

        for s_short_education in self.cv_data["content"]["short_education"]:
            short_education_str += r"""
                                \begin{onecolentry}
                                """
            short_education_str += r"""\textbf{""" + s_short_education["issuer"] + "}, "
            for certificate in s_short_education["certificates"]:
                short_education_str += certificate
                short_education_str += r"""
                                    \kern 5.0 pt%"""
                if certificate != s_short_education["certificates"][-1]:
                    short_education_str += r"""
                                        \AND% 
                                        \kern 5.0 pt%
                                        """
            short_education_str += r"""
                                \end{onecolentry}
                                """
        short_education_str += r"""
                            \vspace{\mainsectionsspace}
                            """
        return short_education_str

    def generate_experience(self):
        experience_str = ""

        experience_str += r"""
    \section{Experience}
            \vspace{\MainHeaderSpace}

    """

        for s_experience in self.cv_data["content"]["experience"]:
            experience_str += r"""
        \begin{twocolentry}{
            """
            experience_str += (
                self.decode_date(s_experience["startDate"])
                + " - "
                + self.decode_date(s_experience["endDate"])
            )
            experience_str += r"""
        }
            \textbf{"""
            experience_str += s_experience["role"]
            experience_str += r"""}, """
            experience_str += s_experience["company"]
            experience_str += r"""
        \end{twocolentry}
        \vspace{\SecHeaderSpace}
        \begin{onecolentry}
            \begin{highlights}
                """
            for responsibility in s_experience["responsibilities"]:
                experience_str += r"""
                \item """
                experience_str += responsibility

            experience_str += r"""
            \end{highlights}
        \end{onecolentry}
        \vspace{\SecAfterHeaderSpace}
        """
        experience_str += r"""
        \vspace{\mainsectionsspace}
        """

        return experience_str

    def generate_projects(self):
        projects_str = ""
        projects_str += r"""
\section{Projects}
        \vspace{\MainHeaderSpace}

    """
        for project in self.cv_data["content"]["projects"]:
            projects_str += r"""
        \begin{twocolentry}{
            \href{"""
            projects_str += project["github_link"]
            projects_str += r"""}{Github}
        }
            \textbf{"""
            projects_str += project["title"]
            projects_str += r"""}
        \end{twocolentry}
        """
            if len(project["responsibilities"]) != 0:
                projects_str += r"""
            \vspace{\SecHeaderSpace}
            \begin{onecolentry}
            \begin{highlights}
            """
                for responsibility in project["responsibilities"]:
                    projects_str += r"""
                \item """
                    projects_str += responsibility
                projects_str += r"""
                            \end{highlights}
                            \end{onecolentry}
                            """
                projects_str += r"""
                            \vspace{\SecAfterHeaderSpace}
                            """
        projects_str += r"""
        \vspace{\mainsectionsspace}
        """
        return projects_str

    def generate_languages(self):
        skills_str = ""
        skills_str += r"""
                    \section{Skills}
                            \vspace{\MainHeaderSpace}

                        \begin{onecolentry}
                                    \textbf{Languages:  }"""

        for language in self.cv_data["content"]["languages"]:
            object = language.replace("#", "\\#")
            if language != self.cv_data["content"]["languages"][-1]:
                skills_str += " " + object + ", "
            else:
                skills_str += "  " + object

        skills_str += r"""
                            \end{onecolentry}

                            \vspace{0.2 cm}
                    """
        return skills_str

    # def generate_technologies(self):
    #     technologies_str = ""

    #     technologies_str += r"""
    #                     \begin{onecolentry}     
    #                                 \textbf{Skills: }
    #                                 """

    #     for technology in self.cv_data["content"]["technologies"]:
    #         object = technology.replace("#", "\\#")
    #         if technology != self.cv_data["content"]["technologies"][-1]:
    #             technologies_str += " " + object + ", "
    #         else:
    #             technologies_str += " " + object

    #     technologies_str += r"""
    #                         \end{onecolentry}
    #                         \vspace{\mainsectionsspace}
    #                 """
    #     return technologies_str

    def generate_technologies(self):
        technologies_str = ""
    
        technologies_str += r"""
            \begin{onecolentry}     
                \textbf{Skills: }
            \end{onecolentry}
            {\normalsize
            \begin{multicols}{4}
                \begin{itemize}[leftmargin=* , labelsep=0.1cm ,topsep=0pt]
        """
    
        for technology in self.cv_data["content"]["technologies"]:
            item = technology.replace("#", "\\#")
            technologies_str += f"\\item {item}\n"
    
        technologies_str += r"""
                \end{itemize}
            \end{multicols}
            }
        """
        return technologies_str


    def add_footer(self):
        return r"""
\end{document}
    """

    def make_cv(self):
        self.cv_str = ""
        self.cv_str += self.add_header()
        self.cv_str += self.generate_personl_info()
        
        # Check if sections exist before including them
        if "sections" in self.cv_data:
            if self.cv_data["sections"].get("objective", True):
                self.cv_str += self.generate_objective()
            if self.cv_data["sections"].get("education", True):
                self.cv_str += self.generate_education()
            if self.cv_data["sections"].get("short_education", True):
                self.cv_str += self.generate_short_education()
            if self.cv_data["sections"].get("languages", True):
                self.cv_str += self.generate_languages()
            if self.cv_data["sections"].get("technologies", True):
                self.cv_str += self.generate_technologies()
            if self.cv_data["sections"].get("experience", True):
                self.cv_str += self.generate_experience()
            if self.cv_data["sections"].get("projects", True):
                self.cv_str += self.generate_projects()
        else:
            # If no sections specified, include all by default
            self.cv_str += self.generate_objective()
            self.cv_str += self.generate_education()
            self.cv_str += self.generate_short_education()
            self.cv_str += self.generate_languages()
            self.cv_str += self.generate_technologies()
            self.cv_str += self.generate_experience()
            self.cv_str += self.generate_projects()

        self.cv_str += self.add_footer()

        return self.cv_str