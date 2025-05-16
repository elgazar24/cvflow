
from flask import Blueprint 
from flask import jsonify
from flask import render_template
from routes.route_path import RoutePath
import db_access



templates = Blueprint('templates', __name__)



@templates.route('/templates')
def templates_index():
    breadcrumbs = [
        {"title": "Templates", "url": "/templates"},
    ]
    return render_template(RoutePath.templates_index , breadcrumbs=breadcrumbs)

@templates.route('/templates/get_templates' , methods=['GET'])
def get_templates():

    # templates = [template.to_dict() for template in db_access.get_all_templates()]

    #    <div class="template-image">
    #       <img src="${template.thumbnailUrl}" alt="${template.name}">
    #       ${isRecommended ? '<span class="recommended-badge">Recommended</span>' : ''}
    #     </div>
    #     <div class="template-info">
    #       <h3>${template.name}</h3>
    #       <div class="template-tags">
    #         ${template.style ? `<span class="template-tag">${capitalizeFirstLetter(template.style)}</span>` : ''}
    #         ${template.experienceLevel ? `<span class="template-tag">${formatExperienceLevel(template.experienceLevel)}</span>` : ''}
    #       </div>
    #     </div>
    #     <button class="preview-btn">Preview</button>
    #   `;

    mock_templates = [
        {
            "id": 1,
            "name": "Template 1",
            "thumbnailUrl": "https://picsum.photos/200/300",
            "style": "Modern",
            "isRecommended": True,
            "sectors": ["IT", "Finance"],
            "experienceLevel": "Intermediate",
        },
        {
            "id": 2,
            "name": "Template 2",
            "thumbnailUrl": "https://picsum.photos/200/300",
            "style": "Minimalist",
            "isRecommended": False,
            "sectors": ["Finance", "Marketing"],
            "experienceLevel": "Beginner",
        },
    ]


    return jsonify({"success": True, "templates": mock_templates}), 200


