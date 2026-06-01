
def calculate_factorial(n=None, query=None):
    """
    Tính giai thừa của một số nguyên không âm n.
    
    Args:
        n (int, optional): Số nguyên không âm cần tính giai thừa
        query (str/int, optional): Tham số thay thế, có thể truyền số trực tiếp hoặc chuỗi số
        
    Returns:
        int: Giai thừa của n (n!)
        
    Raises:
        ValueError: Nếu không truyền tham số hợp lệ hoặc n là số nguyên âm
    """
    # Xử lý tham số: ưu tiên n, nếu không có thì dùng query
    value = n if n is not None else query
    
    if value is None:
        raise ValueError("Cần truyền tham số n hoặc query để tính giai thừa")
    
    # Chuyển đổi sang int nếu là chuỗi
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            raise ValueError(f"Không thể chuyển đổi '{value}' thành số nguyên")
    
    # Kiểm tra kiểu dữ liệu
    if not isinstance(value, int):
        raise TypeError(f"Tham số phải là số nguyên, nhận được: {type(value)}")
    
    # Kiểm tra số không âm
    if value < 0:
        raise ValueError("Giai thừa không được định nghĩa cho số âm")
    
    # Trường hợp đặc biệt
    if value == 0 or value == 1:
        return 1
    
    # Tính giai thừa bằng vòng lặp (tối ưu hơn đệ quy)
    result = 1
    for i in range(2, value + 1):
        result *= i
    
    return result
