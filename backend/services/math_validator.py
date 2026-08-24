import sympy
import re

def extract_numeric_value(text: str):
    """
    Attempt to extract a numeric value from text.
    Handles percentages, fractions, and simple decimals.
    """
    text = text.strip().replace(',', '')
    
    # Handle percentage
    if text.endswith('%'):
        try:
            return sympy.Rational(text[:-1]) / 100
        except:
            pass
            
    # Handle fractions (e.g. 1/2)
    if '/' in text:
        try:
            parts = text.split('/')
            if len(parts) == 2:
                return sympy.Rational(parts[0].strip(), parts[1].strip())
        except:
            pass
            
    # Handle basic floats/ints
    try:
        return sympy.Rational(str(float(text)))
    except:
        pass
        
    return None

def validate_math_answer(llm_answer: str, intended_answer: str) -> bool:
    """
    Use sympy to verify if two numeric answers are mathematically equivalent.
    """
    val1 = extract_numeric_value(llm_answer)
    val2 = extract_numeric_value(intended_answer)
    
    if val1 is not None and val2 is not None:
        return bool(sympy.simplify(val1 - val2) == 0)
        
    # Fallback to simple string matching if not numeric
    # Remove whitespace and lowercase
    clean1 = re.sub(r'\s+', '', llm_answer).lower()
    clean2 = re.sub(r'\s+', '', intended_answer).lower()
    return clean1 == clean2
