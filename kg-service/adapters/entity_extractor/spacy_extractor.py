from typing import List
import spacy
from core.ports.entity_extractor import EntityExtractorPort
from core.domain.models import Entity, Relation

class SpacyEntityExtractor(EntityExtractorPort):
    def __init__(self, model_name: str = "en_core_web_sm", entity_types: List[str] = None):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)
        
        self.entity_types = entity_types or ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT"]
    
    async def extract_entities(self, text: str) -> List[Entity]:
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in self.entity_types:
                entity = Entity(
                    name=ent.text,
                    entity_type=ent.label_,
                    confidence=0.8,
                    properties={
                        "start_char": ent.start_char,
                        "end_char": ent.end_char
                    }
                )
                entities.append(entity)
        
        return entities
    
    async def extract_relations(self, text: str, entities: List[Entity]) -> List[Relation]:
        relations = []
        entity_names = [e.name for e in entities]
        
        for i, ent1 in enumerate(entity_names):
            for ent2 in entity_names[i+1:]:
                if ent1 in text and ent2 in text:
                    pos1 = text.find(ent1)
                    pos2 = text.find(ent2)
                    
                    if abs(pos1 - pos2) < 200:
                        relation = Relation(
                            source=ent1,
                            target=ent2,
                            relation_type="RELATED_TO",
                            confidence=0.6,
                            properties={"distance": abs(pos1 - pos2)}
                        )
                        relations.append(relation)
        
        return relations
