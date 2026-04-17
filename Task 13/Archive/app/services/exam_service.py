import random

from app.utils.text_utils import extract_keywords, split_sentences


class ExamService:
    def __init__(self, rag_service):
        self.rag_service = rag_service

    def generate_questions(self, topic, count):
        prompt = topic.strip() if topic and topic.strip() else "core concepts"
        retrieved = self.rag_service.retrieve(prompt, top_k=max(6, count + 2))

        if not retrieved:
            return []

        corpus = " ".join(item.get("text", "") for item in retrieved)
        keywords = extract_keywords(corpus, limit=max(10, count * 2))
        sentences = [s for s in split_sentences(corpus) if len(s) > 45]

        if not sentences:
            sentences = [item.get("text", "")[:220] for item in retrieved if item.get("text")]

        random.seed(len(corpus) + count)

        questions = []
        for i in range(count):
            sentence = sentences[i % len(sentences)] if sentences else ""
            key = keywords[i % len(keywords)] if keywords else f"concept-{i + 1}"
            alt = keywords[(i + 1) % len(keywords)] if len(keywords) > 1 else "related idea"
            alt2 = keywords[(i + 2) % len(keywords)] if len(keywords) > 2 else "supporting topic"

            mode = i % 3
            if mode == 0:
                q = {
                    "type": "Short Answer",
                    "question": f"Explain the significance of '{key}' based on the study material.",
                    "answer_guide": sentence,
                }
            elif mode == 1:
                q = {
                    "type": "Conceptual",
                    "question": f"How does '{key}' connect with '{alt}' in this topic area?",
                    "answer_guide": sentence,
                }
            else:
                options = [key, alt, alt2, "none of the above"]
                random.shuffle(options)
                q = {
                    "type": "MCQ",
                    "question": f"Which term is most directly discussed with this idea: {sentence[:90]}...?",
                    "options": options,
                    "correct_answer": key,
                    "answer_guide": sentence,
                }

            questions.append(q)

        return questions
