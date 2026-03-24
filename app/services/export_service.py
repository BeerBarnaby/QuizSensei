"""
ExportService - Handles conversion of generated questions into various external formats.
Supported: Moodle XML, JSON (Standard).
Future: PDF, XLSX.
"""
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ExportService:
    """
    Service responsible for transforming database question records into
    standardized formats for teachers to use in other LMS platforms.
    """

    def export_to_moodle_xml(self, questions: List[Dict[str, Any]], category_name: str = "QuizSensei Export") -> str:
        """
        Converts a list of questions into Moodle XML format.
        This allows teachers to import the questions directly into Moodle.
        """
        quiz = ET.Element("quiz")

        # 1. Add Category header
        question_cat = ET.SubElement(quiz, "question", {"type": "category"})
        category = ET.SubElement(question_cat, "category")
        text_cat = ET.SubElement(category, "text")
        text_cat.text = f"$course$/top/{category_name}"

        # 2. Process each question
        for q_data in questions:
            # Assume q_data follows the Question model or its JSON payload
            q_node = ET.SubElement(quiz, "question", {"type": "multichoice"})
            
            # Name
            name = ET.SubElement(q_node, "name")
            name_text = ET.SubElement(name, "text")
            name_text.text = f"QS_{q_data.get('id', 'unk')[:8]}"
            
            # Question Text
            qtext = ET.SubElement(q_node, "questiontext", {"format": "html"})
            text_node = ET.SubElement(qtext, "text")
            text_node.text = f"<![CDATA[{q_data.get('stem', '')}]]>"
            
            # Metadata / Feedback
            generalfeedback = ET.SubElement(q_node, "generalfeedback", {"format": "html"})
            gf_text = ET.SubElement(generalfeedback, "text")
            gf_text.text = f"<![CDATA[{q_data.get('rationale_for_correct_answer', '')}]]>"
            
            # Settings
            ET.SubElement(q_node, "defaultgrade").text = "1.0000000"
            ET.SubElement(q_node, "penalty").text = "0.3333333"
            ET.SubElement(q_node, "hidden").text = "0"
            ET.SubElement(q_node, "single").text = "true"
            ET.SubElement(q_node, "shuffleanswers").text = "true"
            ET.SubElement(q_node, "answernumbering").text = "abc"

            # Choices
            # internal format: choices list of dict {'key': 'A', 'text': '...'}
            choices = q_data.get("choices", [])
            correct_key = q_data.get("correct_answer")
            distractor_map = q_data.get("distractor_map", {})

            for choice in choices:
                key = choice.get("key")
                text = choice.get("text")
                is_correct = (key == correct_key)
                
                fraction = "100" if is_correct else "0"
                answer_node = ET.SubElement(q_node, "answer", {"fraction": fraction, "format": "html"})
                ans_text = ET.SubElement(answer_node, "text")
                ans_text.text = f"<![CDATA[{text}]]>"
                
                # Feedback for this specific choice (Misconception info for wrong ones)
                feedback = ET.SubElement(answer_node, "feedback", {"format": "html"})
                fb_text = ET.SubElement(feedback, "text")
                
                if not is_correct:
                    d_info = distractor_map.get(key, {})
                    misconception = d_info.get("misconception", "")
                    why = d_info.get("why_plausible", "")
                    fb_content = f"ผิด: {why}"
                    if misconception:
                        fb_content += f" (ความเข้าใจผิด: {misconception})"
                    fb_text.text = f"<![CDATA[{fb_content}]]>"
                else:
                    fb_text.text = f"<![CDATA[ถูกต้อง! {q_data.get('rationale_for_correct_answer', '')}]]>"

        # Convert to pretty XML string
        xml_str = ET.tostring(quiz, encoding='utf-8')
        reparsed = minidom.parseString(xml_str)
        return reparsed.toprettyxml(indent="  ")

    def export_to_json_standard(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Returns a clean JSON structure of the questions.
        Useful for custom integrations or third-party apps.
        """
        return {
            "metadata": {
                "source": "QuizSensei",
                "export_date": datetime.utcnow().isoformat(),
                "count": len(questions)
            },
            "questions": questions
        }
