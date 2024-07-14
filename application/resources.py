from flask_restful import Api, Resource, reqparse
from .model import *
from .database import db


api = Api()

# For request body
parser = reqparse.RequestParser()

parser.add_argument("section_id")
parser.add_argument("section_name")
parser.add_argument("section_description")


class SectionsApi(Resource):
    def get(self):
        all_sections = Sections.query.all()
        all_sections_data = []
        for sec in all_sections:
            sec_info = {}
            sec_info["section_id"] = sec.section_id
            sec_info["section_name"] = sec.section_name
            sec_info["date_created"] = f"{sec.date_created.strftime("%d")}-{sec.date_created.strftime("%b")}-{sec.date_created.strftime("%Y")}"
            sec_info["last_updated"] = f"{sec.last_updated.strftime("%d")}-{sec.last_updated.strftime("%b")}-{sec.last_updated.strftime("%Y")}"
            sec_info["description"] = sec.description
            all_sections_data.append(sec_info)

        return all_sections_data

    def post(self):
        section_data = parser.parse_args()
        existing_section = Sections.query.get(section_data["section_id"])
        if existing_section:
            return "This Section id already exists.", 400
        else:
            create_section = Sections(section_id = section_data["section_id"],
                                        section_name = section_data["section_name"],
                                        description = section_data["section_description"])
            db.session.add(create_section)
            db.session.commit()
        return "Section created successfully", 201

    def put(self):
        section_data = parser.parse_args()
        this_section = Sections.query.get(section_data["section_id"])
        if this_section:
            this_section.section_name = section_data["section_name"]
            this_section.last_updated = datetime.now()
            this_section.description = section_data["section_description"]
            db.session.commit()
        else:
            return f"No such section exists with Section Id: {section_data["section_id"]}", 404

        return "Section successfully updated"

    def delete(self):
        section_data = parser.parse_args()
        this_section = Sections.query.get(section_data["section_id"])
        if this_section:
            db.session.delete(this_section)
            db.session.commit()
            return "Section successfully deleted"
        else:
            return f"No such section exists with Section Id: {section_data["section_id"]}", 404
        


# Api end points
api.add_resource(SectionsApi, "/api/sections")