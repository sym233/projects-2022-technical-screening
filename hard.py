"""
Inside conditions.json, you will see a subset of UNSW courses mapped to their 
corresponding text conditions. We have slightly modified the text conditions
to make them simpler compared to their original versions.

Your task is to complete the is_unlocked function which helps students determine 
if their course can be taken or not. 

We will run our hidden tests on your submission and look at your success rate.
We will only test for courses inside conditions.json. We will also look over the 
code by eye.

NOTE: This challenge is EXTREMELY hard and we are not expecting anyone to pass all
our tests. In fact, we are not expecting many people to even attempt this.
For complete transparency, this is worth more than the easy challenge. 
A good solution is favourable but does not guarantee a spot in Projects because
we will also consider many other criteria.
"""
import json
import re
from typing import List, Optional, Dict
# List and Dict is deprecated since py3.9

class Prereq:
    def satisfy(self, courses_list: List[str]) -> bool:
        return True
    def __str__(self) -> str:
        return "Prereq()"
class CoursePrereq(Prereq):
    course: str
    def __init__(self, course) -> None:
        super().__init__()
        self.course = course
    def satisfy(self, courses_list: List[str]) -> bool:
        return self.course in courses_list
    def __str__(self) -> str:
        return f'CoursePrereq({self.course})'
class CreditPrereq(Prereq):
    credit_required: int
    credit_per_course = 6
    course_range: Optional[List[str]]
    def __init__(self, credit_required: int, course_range: Optional[List[str]]) -> None:
        super().__init__()
        self.credit_required = credit_required
        self.course_range = course_range
    def satisfy(self, courses_list: List[str]) -> bool:
        total_credit = 0
        for course in courses_list:
            if self.course_range == None or course in self.course_range:
                total_credit += self.credit_per_course
        return total_credit >= self.credit_required
    def __str__(self) -> str:
        cond = f' of {self.course_range}' if self.course_range else ''
        return f'CreditPrereq({self.credit_required}u{cond})'
class CondPrereq(CreditPrereq):
    level: Optional[int] = None
    area: Optional[str] = None
    def __init__(self, credit_required: int, level: Optional[int] = None, area: Optional[int] = None) -> None:
        super().__init__(credit_required, None)
        self.level = level
        self.area = area
    def satisfy(self, courses_list: List[str]) -> bool:
        satisfied_courses: List[str] = []
        for course in courses_list:
            cond = self.area == None or self.area == course[:4]
            # COMP
            cond = cond and self.level == None or self.level == int(course[4])
            # COMPwxyz
            if cond:
                satisfied_courses.append(course)
        return super().satisfy(satisfied_courses)
    def __str__(self) -> str:
        cond = f' level {self.level}' if self.level else ''
        cond += f' {self.area}' or ''
        cond = cond and f' of{cond}'
        return f'CondPrereq({self.credit_required}u{cond})'
class PrereqAnd(Prereq):
    lhs: Prereq
    rhs: Prereq
    def __init__(self, lhs: Prereq, rhs: Prereq) -> None:
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs
    def satisfy(self, courses_list: List[str]) -> bool:
        return self.lhs.satisfy(courses_list) and self.rhs.satisfy(courses_list)
    def __str__(self) -> str:
        return f'PrereqAnd({self.lhs} and {self.rhs})'
class PrereqOr(Prereq):
    lhs: Prereq
    rhs: Prereq
    def __init__(self, lhs: Prereq, rhs: Prereq) -> None:
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs
    def satisfy(self, courses_list: List[str]) -> bool:
        return self.lhs.satisfy(courses_list) or self.rhs.satisfy(courses_list)
    def __str__(self) -> str:
        return f'PrereqOr({self.lhs} or {self.rhs})'

def handle_logical_op(operands: List[Prereq], operators: List[str]) -> None:
    while operators and operators[-1] in ['AND', 'OR']:
        op = operators.pop()
        rhs = operands.pop()
        lhs = operands.pop()
        if op == 'AND':
            prereq = PrereqAnd(lhs, rhs)
        else:
            prereq = PrereqOr(lhs, rhs)
        operands.append(prereq)

def parse_prereq(sentence: str) -> Prereq:
    stack: List[Prereq] = []
    stack_logical_op: List[str] = []
    # possible element: 'AND', 'OR', '('
    wait_for_cond: bool = False
    credit: Optional[int] = None
    sentence = sentence.strip()
    while sentence != '':
        if sentence.startswith('('):
            stack_logical_op.append('(')
            sentence = sentence[1:].strip()
            continue
        if sentence.startswith(')'):
            assert stack_logical_op and stack_logical_op[-1] == '('
            stack_logical_op.pop()
            handle_logical_op(stack, stack_logical_op)
        m = re.match(r'^\w+\b', sentence)
        if m == None:
            # the first char may be punctuation, skip
            sentence = sentence[1:].strip()
            continue
        elif re.match(r'^\d{4}$', m[0]):
            # match a 4-digit number, treated as course name
            course = 'COMP' + m[0]
            stack.append(CoursePrereq(course))
            if stack_logical_op and stack_logical_op[-1] in ['AND', 'OR']:
                handle_logical_op(stack, stack_logical_op)
            sentence = sentence[m.end():].strip()
            continue
        elif re.match(r'^[A-Z]{4}\d{4}$', m[0]):
            # match a course name
            course = m[0]
            stack.append(CoursePrereq(course))
            if stack_logical_op and stack_logical_op[-1] in ['AND', 'OR']:
                handle_logical_op(stack, stack_logical_op)
            sentence = sentence[m.end():].strip()
            continue
        elif re.match(r'^\d{1,3}$', m[0]):
            # match a 1-to-3-digit number, 
            # treated as units of credit if no number met before
            credit = int(m[0])
            wait_for_cond = True
            sentence = sentence[m.end():].strip()
            continue
        elif m[0] == 'IN':
            if wait_for_cond:
                # credit must be int
                # next must be condition of credit
                wait_for_cond = False
                rest_sentence = sentence[m.end():].strip()
                if rest_sentence.startswith('('):
                    # * units of credit in (COMP6443, ...)
                    right_parenthese = rest_sentence.find(')')
                    possible_courses_list = re.split(r'\s*\,?\s+', rest_sentence[1: right_parenthese])
                    courses_list: List[str] = []
                    for course in possible_courses_list:
                        if re.match(r'^\d{4}$', course):
                            courses_list.append(f'COMP{course}')
                        elif re.match(r'^[A-Z]{4}\d{4}$', course):
                            courses_list.append(course)
                    stack.append(CreditPrereq(credit, courses_list))
                    if stack_logical_op and stack_logical_op[-1] in ['AND', 'OR']:
                        handle_logical_op(stack, stack_logical_op)
                    sentence = rest_sentence[right_parenthese + 1:].strip()
                    continue
                else:
                    m2 = re.match(r'^(LEVEL\s(\d+)\s)?([A-Z]{4})\b', rest_sentence)
                    # * units of credit in (level *)? COMP courses
                    if m2:
                        level: Optional[int] = m2.groups()[1] and int(m2.groups()[1])
                        area = m2.groups()[2]
                        stack.append(CondPrereq(credit, level, area))
                        if stack_logical_op and stack_logical_op[-1] in ['AND', 'OR']:
                            handle_logical_op(stack, stack_logical_op)
                        sentence = sentence[m2.end():].strip()
                        continue
            # otherwise omit it
            sentence = sentence[m.end():].strip()
            continue
        elif m[0] in ['AND', 'OR']:
            if wait_for_cond:
                wait_for_cond = False
                stack.append(CreditPrereq(credit, None))
            stack_logical_op.append(m[0])
            sentence = sentence[m.end():].strip()
            continue
        else:
            # unknown word, skip
            sentence = sentence[m.end():].strip()
    if wait_for_cond:
        wait_for_cond = False
        stack.append(CreditPrereq(credit, None))
        handle_logical_op(stack, stack_logical_op)
    if stack and len(stack) == 1:
        return stack[0]
    else:
        return Prereq()

prereqs: Dict[str, Prereq] = {}

# NOTE: DO NOT EDIT conditions.json
with open("./conditions.json") as f:
    CONDITIONS = json.load(f)
    f.close()

for course, desc in CONDITIONS.items():
    course = str(course).upper().strip()
    sentence = str(desc).upper().strip() 
    sentence = ' '.join(re.split(r'\s+', sentence))
    # remove continuous spaces
    if course.startswith('-'):
        continue
    prereqs[course] = parse_prereq(sentence)


def is_unlocked(courses_list, target_course):
    """Given a list of course codes a student has taken, return true if the target_course 
    can be unlocked by them.
    
    You do not have to do any error checking on the inputs and can assume that
    the target_course always exists inside conditions.json

    You can assume all courses are worth 6 units of credit
    """
    
    # TODO: COMPLETE THIS FUNCTION!!!
    
    prereq = prereqs[target_course]
    return prereq.satisfy(courses_list)




    