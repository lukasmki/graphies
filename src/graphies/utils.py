def base16(n: int) -> list[int]:
    if n == 0:
        return [0]
    elif n > 0:
        digits: list[int] = []
        while n > 0:
            digits.append(n % 16)
            n //= 16
        return digits
    else:
        raise ValueError("n must be nonzero")
