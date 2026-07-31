def calculate_mastery(correct_count: int, wrong_count: int) -> tuple:
    if correct_count >= 2:
        return 1.00, "mastered"
    elif wrong_count >= 2:
        return 0.00, "weak"
    elif correct_count == 0 and wrong_count == 0:
        return 0.00, "pending"
    else:
        total = correct_count + wrong_count
        master_level = (correct_count * 0.5) / total
        return round(master_level, 2), "pending"