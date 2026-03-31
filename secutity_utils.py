def calculate_fraud_score(amount, user_avg, attempts, location, ip_location, device_match):
    score = 0
    reasons = []

    # High amount vs average
    if amount > user_avg * 3:
        score += 40
        reasons.append("Amount unusually high")

    # Too many attempts
    if attempts > 3:
        score += 30
        reasons.append("High transaction frequency")

    # Location mismatch
    if location.lower() != ip_location.lower():
        score += 40
        reasons.append("Location mismatch (IP vs Input)")

    # Unknown device
    if not device_match:
        score += 25
        reasons.append("Unrecognized device")

    return score, reasons