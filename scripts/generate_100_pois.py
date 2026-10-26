import json
from pathlib import Path

# Danh sách 100 địa điểm có thật tại TP.HCM với toạ độ thực, mô tả sâu sắc và thuyết minh truyền cảm
POIS_DATA = [
    # --- Quận 1 & Trung tâm Lịch sử ---
    (
        "dinh-doc-lap", "historical", "Dinh Độc Lập", 10.7769, 106.6953, 5,
        "https://images.unsplash.com/photo-1583417319070-4a69db38a482?auto=format&fit=crop&w=800&q=80",
        "Di tích lịch sử quốc gia đặc biệt, công trình kiến trúc biểu tượng ghi dấu thời khắc thống nhất đất nước.",
        "Chào mừng bạn đến với Dinh Độc Lập, kiệt tác kiến trúc của kiến trúc sư Ngô Viết Thụ. Công trình hài hòa giữa triết lý phương Đông và phong cách hiện đại phương Tây, từng là nơi chứng kiến sự kiện lịch sử trưa ngày 30 tháng 4 năm 1975."
    ),
    (
        "nha-tho-duc-ba", "religious", "Nhà thờ Đức Bà Sài Gòn", 10.7798, 106.6990, 5,
        "https://images.unsplash.com/photo-1569154941061-e231b4725ef1?auto=format&fit=crop&w=800&q=80",
        "Vương cung thánh đường Chính tòa cổ kính với kiến trúc Roman pha trộn Gothic tuyệt mỹ giữa lòng thành phố.",
        "Bạn đang chiêm ngưỡng Nhà thờ Đức Bà Sài Gòn, khánh thành năm 1880. Toàn bộ gạch ngói xây dựng đều được vận chuyển trực tiếp từ Marseille nước Pháp, giữ nguyên sắc đỏ hồng đặc trưng qua hơn một thế kỷ thăng trầm cùng đô thị."
    ),
    (
        "buu-dien-trung-tam", "historical", "Bưu điện Trung tâm Sài Gòn", 10.7799, 106.6999, 5,
        "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=800&q=80",
        "Công trình bưu điện phong cách phục hưng tuyệt đẹp, điểm hẹn check-in và gửi thư lưu niệm của du khách toàn cầu.",
        "Bưu điện Trung tâm Sài Gòn được xây dựng vào cuối thế kỷ 19. Nơi đây gây ấn tượng bởi vòm trần cong rộng lớn lợp kính lấy sáng, hệ thống khung sắt tinh xảo và những bản đồ cổ vẽ tay phác họa tuyến đường liên lạc Đông Dương xưa."
    ),
    (
        "cho-ben-thanh", "market", "Chợ Bến Thành", 10.7725, 106.6980, 5,
        "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=800&q=80",
        "Ngôi chợ biểu tượng hơn 100 năm tuổi với tháp đồng hồ 4 mặt huyền thoại, nơi hội tụ tinh hoa ẩm thực và mua sắm.",
        "Chợ Bến Thành là trái tim giao thương của Sài Gòn từ năm 1914. Bốn mặt cổng Đông Tây Nam Bắc hướng ra các đại lộ trung tâm luôn nhộn nhịp tiếng rao, rực rỡ sắc màu vải vóc, đồ thủ công mỹ nghệ và hương vị ẩm thực ba miền."
    ),
    (
        "nha-hat-thanh-pho", "historical", "Nhà hát Thành phố", 10.7766, 106.7032, 4,
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=800&q=80",
        "Công trình kiến trúc Flamboyant Pháp hoa lệ, trung tâm biểu diễn nghệ thuật hàn lâm đỉnh cao tại Sài Gòn.",
        "Khánh thành vào năm 1900, Nhà hát Lớn TP.HCM mang đậm dấu ấn phong cách rực rỡ Flamboyant Pháp. Mặt tiền trang trí phù điêu nữ thần nghệ thuật cùng nội thất âm học đỉnh cao là điểm hẹn của các vở diễn kịch, ballet và hòa nhạc thính phòng."
    ),
    (
        "tru-so-ubnd", "historical", "Trụ sở UBND Thành phố", 10.7768, 106.7011, 4,
        "https://images.unsplash.com/photo-1574044733355-618e47c0b020?auto=format&fit=crop&w=800&q=80",
        "Tòa thị chính cổ kính với kiến trúc lâu đài đài các, đặt tại đầu phố đi bộ Nguyễn Huệ.",
        "Trụ sở Ủy ban Nhân dân TP.HCM hoàn thành năm 1909 với tháp chuông trung tâm và các bức phù điêu nữ thần Marianne. Về đêm, ánh đèn chiếu sáng nghệ thuật biến tòa nhà thành một cung điện lung linh soi bóng tượng đài Bác Hồ."
    ),
    (
        "pho-di-bo-nguyen-hue", "public-space", "Phố đi bộ Nguyễn Huệ", 10.7741, 106.7039, 5,
        "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=800&q=80",
        "Quảng trường đi bộ hiện đại dài gần 1km hướng ra sông Sài Gòn, tâm điểm lễ hội và văn hóa giới trẻ.",
        "Phố đi bộ Nguyễn Huệ trước kia là kênh đào Chợ Vải sầm uất. Ngày nay, quảng trường lát đá granite với đài phun nước nhạc nước, cây xanh và các quán cà phê chung cư cổ kính tạo nên không gian sinh hoạt cộng đồng sôi động nhất thành phố."
    ),
    (
        "ben-nha-rong", "historical", "Bảo tàng Hồ Chí Minh - Bến Nhà Rồng", 10.7682, 106.7068, 5,
        "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=800&q=80",
        "Địa danh lịch sử nơi người thanh niên Nguyễn Tất Thành ra đi tìm đường cứu nước năm 1911.",
        "Tọa lạc bên ngã ba sông Sài Gòn, tòa nhà mang đôi rồng chầu mặt trăng trên nóc vốn là trụ sở hãng tàu Messageries Maritimes. Nơi đây hiện lưu giữ hàng ngàn hiện vật quý giá tái hiện cuộc đời và sự nghiệp vĩ đại của Chủ tịch Hồ Chí Minh."
    ),
    (
        "bao-tang-my-thuat", "museum", "Bảo tàng Mỹ thuật TP.HCM", 10.7700, 106.6992, 4,
        "https://images.unsplash.com/photo-1544967082-d9d25d867d66?auto=format&fit=crop&w=800&q=80",
        "Dinh thự hoa lệ của thương nhân Hứa Bổn Hòa kết hợp tinh tế giữa Art Deco phương Tây và phong thủy Á Đông.",
        "Bảo tàng Mỹ thuật gồm ba tòa dinh thự tuyệt đẹp với thang máy cổ điển, sàn gạch bông hoa văn và các ô cửa kính màu. Nơi đây trưng bày các bộ sưu tập hội họa, điêu khắc vô giá từ thời tiền sử đến mỹ thuật đương đại Việt Nam."
    ),
    (
        "bao-tang-chung-tich", "museum", "Bảo tàng Chứng tích Chiến tranh", 10.7794, 106.6922, 5,
        "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=800&q=80",
        "Bảo tàng thu hút đông đảo du khách quốc tế với thông điệp hòa bình và chứng tích lịch sử sâu sắc.",
        "Bảo tàng Chứng tích Chiến tranh là một trong những điểm đến xúc động nhất của Sài Gòn. Những hiện vật, hình ảnh và tư liệu chiến tranh tại đây nhắc nhở nhân loại về giá trị thiêng liêng của hòa bình và sự kiên cường của nhân dân Việt Nam."
    ),
    (
        "bao-tang-lich-su", "museum", "Bảo tàng Lịch sử TP.HCM", 10.7876, 106.7051, 4,
        "https://images.unsplash.com/photo-1565034946487-077786996e27?auto=format&fit=crop&w=800&q=80",
        "Công trình kiến trúc Đông Dương độc đáo lưu giữ tiến trình phát triển hàng ngàn năm của dân tộc.",
        "Nằm trong khuôn viên Thảo Cầm Viên xanh mát, Bảo tàng Lịch sử mang phong cách kiến trúc Đông Dương do kiến trúc sư Delaval thiết kế. Nơi đây trưng bày thi hài xác ướp Xóm Cải cùng nhiều cổ vật quý giá của văn hóa Óc Eo, Champa."
    ),
    (
        "thao-cam-vien", "public-space", "Thảo Cầm Viên Sài Gòn", 10.7875, 106.7055, 4,
        "https://images.unsplash.com/photo-1534567153574-2b12153a87f0?auto=format&fit=crop&w=800&q=80",
        "Vườn bách thảo lâu đời thứ tám trên thế giới, lá phổi xanh lịch sử giữa trung tâm thành phố.",
        "Xây dựng từ năm 1864, Thảo Cầm Viên là mái nhà của hàng trăm loài động thực vật quý hiếm và cây cổ thụ trăm tuổi. Không gian rợp bóng mát này là ký ức tuổi thơ thân thương của biết bao thế hệ người dân TP.HCM."
    ),
    (
        "ho-con-rua", "public-space", "Hồ Con Rùa", 10.7828, 106.6958, 3,
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80",
        "Vòng xoay đài phun nước hình cánh hoa xòe, địa điểm tụ tập ăn vặt nổi tiếng của giới trẻ Sài thành.",
        "Hồ Con Rùa có tên chính thức là Công trường Quốc tế, xây dựng cuối thập niên 1960. Kiến trúc tháp bê tông vươn cao mô phỏng đài sen cùng hồ nước bao quanh là nơi hò hẹn quen thuộc để thưởng thức bánh tráng nướng, trà đào vỉa hè."
    ),
    (
        "cong-vien-tao-dan", "public-space", "Công viên Tao Đàn", 10.7745, 106.6925, 4,
        "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=800&q=80",
        "Công viên rợp bóng hàng cây sao cổ thụ, nơi giao lưu chim cảnh và đền tưởng niệm các vua Hùng.",
        "Tao Đàn là một trong những công viên thanh bình và rộng lớn nhất Sài Gòn. Mỗi sớm mai, nơi đây rộn rã tiếng chim hót từ câu lạc bộ chim cảnh, tiếng cười nói tập thể dục của người cao tuổi dưới bóng những tán cây cổ thụ trăm năm."
    ),
    (
        "cong-vien-23-thang-9", "public-space", "Công viên 23 Tháng 9", 10.7689, 106.6934, 3,
        "https://images.unsplash.com/photo-1519331379826-f10be5486c6f?auto=format&fit=crop&w=800&q=80",
        "Dải xanh nối liền khu phố Tây Bùi Viện và chợ Bến Thành, từng là ga xe lửa Sài Gòn xưa.",
        "Công viên 23 Tháng 9 là điểm giao thoa văn hóa quốc tế nhộn nhịp. Du khách từ khắp nơi trên thế giới dạo bước dưới bóng mát, tham quan các hội chợ ẩm thực cuối tuần và trò chuyện giao lưu ngoại ngữ cùng sinh viên thành phố."
    ),
    (
        "cot-co-thu-ngu", "historical", "Cột cờ Thủ Ngữ", 10.7712, 106.7065, 3,
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=800&q=80",
        "Cột cờ hoa tiêu hàng hải hơn 150 năm tuổi đứng sừng sững nơi ngã ba rạch Bến Nghé đổ vào sông Sài Gòn.",
        "Xây dựng năm 1865, Cột cờ Thủ Ngữ đóng vai trò trạm tín hiệu hướng dẫn tàu bè ra vào thương cảng Sài Gòn. Di tích này cùng bến Bạch Đằng tạo nên tầm nhìn khoáng đạt về phía trung tâm tài chính và bán đảo Thủ Thiêm."
    ),
    (
        "cau-mong", "historical", "Cầu Mống", 10.7686, 106.7037, 4,
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80",
        "Cây cầu vòm sắt màu xanh ngọc do công ty Eiffel xây dựng thế kỷ 19, điểm ngắm hoàng hôn lãng mạn.",
        "Cầu Mống bắc qua kênh Bến Nghé nối Quận 1 và Quận 4, hoàn thành năm 1894. Với kết cấu vòm thép cổ điển sơn màu xanh ngọc bích trang nhã, cây cầu dành cho người đi bộ này là tọa độ chụp ảnh và ngắm hoàng hôn được yêu thích bậc nhất."
    ),
    (
        "pho-tay-bui-vien", "public-space", "Phố đi bộ Bùi Viện", 10.7672, 106.6938, 4,
        "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=800&q=80",
        "Con phố 'không ngủ' rực rỡ ánh đèn neon, âm nhạc đường phố và thiên đường ẩm thực đêm của giới trẻ.",
        "Khi hoàng hôn buông xuống, phố Bùi Viện biến thành một bữa tiệc âm thanh và ánh sáng cuồng nhiệt. Du khách ngồi trên những chiếc ghế con vỉa hè nhâm nhi bia mát lạnh, thưởng thức hải sản nướng và hòa mình vào làn sóng âm nhạc đa sắc tộc."
    ),
    (
        "ben-bach-dang", "public-space", "Bến Bạch Đằng & Công viên Bến Bạch Đằng", 10.7735, 106.7072, 5,
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
        "Dải công viên ven sông hiện đại bậc nhất, nơi đón gió sông Sài Gòn và trải nghiệm Waterbus đường thủy.",
        "Công viên Bến Bạch Đằng vừa được chỉnh trang hiện đại với thảm cỏ xanh mướt, lối đi dạo lộng gió ngắm cầu Ba Son và các tòa cao ốc Thủ Thiêm. Đây cũng là ga tàu thủy Saigon Waterbus đưa du khách du ngoạn ngắm thành phố từ mặt nước."
    ),
    (
        "cau-ba-son", "historical", "Cầu Ba Son (Cầu Thủ Thiêm 2)", 10.7797, 106.7103, 4,
        "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80",
        "Cây cầu dây văng biểu tượng mới mang hình cánh buồm đón gió vượt sông Sài Gòn sang bán đảo Thủ Thiêm.",
        "Cầu Ba Son khánh thành năm 2022 với kiến trúc dây văng hình cánh buồm trắng kiêu hãnh. Tên gọi Ba Son nhằm tri ân cái nôi của ngành công nghiệp đóng tàu và phong trào công nhân cách mạng Việt Nam thế kỷ 20."
    ),
    (
        "bitexco-tower", "historical", "Tòa tháp Bitexco Financial Tower", 10.7716, 106.7044, 4,
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80",
        "Biểu tượng kinh tế năng động của TP.HCM lấy cảm hứng từ búp sen truyền thống vươn lên bầu trời xanh.",
        "Tháp Bitexco cao 262 mét từng là tòa nhà cao nhất Việt Nam khi khánh thành năm 2010. Đài quan sát Skydeck trên tầng 49 và sân đỗ trực thăng vươn ra khỏi thân tháp mang lại góc nhìn toàn cảnh 360 độ ngoạn mục về đô thị Sài Gòn."
    ),
    (
        "cho-tan-dinh", "market", "Chợ Tân Định", 10.7901, 106.6908, 4,
        "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
        "Ngôi chợ di sản gần 100 năm tuổi, nổi tiếng với vựa vải phong phú và thiên đường ẩm thực đêm trứ danh.",
        "Chợ Tân Định xây dựng năm 1926 nổi bật với cổng vòm ba tháp chuông uy nghiêm. Khu chợ nức tiếng gần xa nhờ chợ vải đầu mối sầm uất và khu ăn uống với món xôi gà, cháo ếch, súp cua thơm lừng níu chân thực khách."
    ),
    (
        "nha-tho-tan-dinh", "religious", "Nhà thờ Tân Định (Nhà thờ Màu Hồng)", 10.7885, 106.6903, 5,
        "https://images.unsplash.com/photo-1548625361-195fe578772a?auto=format&fit=crop&w=800&q=80",
        "Công trình kiến trúc Gothic rực rỡ với sắc hồng cổ tích thu hút du khách khắp năm châu.",
        "Được mệnh danh là 'Nhà thờ màu hồng', công trình khánh thành năm 1876 kết hợp tài tình giữa Gothic, Romanesque và Baroque. Tháp chuông cao 52 mét màu hồng ngọt ngào khiến nhà thờ trở thành biểu tượng thị giác độc đáo của TP.HCM."
    ),
    (
        "khach-san-continental", "historical", "Khách sạn Continental Saigon", 10.7772, 106.7028, 4,
        "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80",
        "Khách sạn cổ nhất Việt Nam xây dựng năm 1880, chứng nhân lịch sử gắn liền văn hào Graham Greene.",
        "Continental Saigon là khách sạn sang trọng đầu tiên của Nam Kỳ. Với khoảng sân vườn rợp bóng hoa sứ trắng và dãy hành lang kiểu thuộc địa lộng gió, đây từng là nơi nhà văn Graham Greene viết nên tiểu thuyết lừng danh 'Người Mỹ trầm lặng'."
    ),
    (
        "khach-san-majestic", "historical", "Khách sạn Majestic Saigon", 10.7728, 106.7061, 4,
        "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=800&q=80",
        "Khách sạn phong cách Art Deco quý phái tọa lạc ngay góc đường Đồng Khởi hướng thẳng ra bến sông.",
        "Xây dựng năm 1925 bởi doanh nhân Hứa Bổn Hòa, Majestic Saigon mang nét đẹp cổ điển hoàng gia Pháp. Quầy bar trên tầng thượng hướng ra khúc quanh sông Sài Gòn là nơi lý tưởng để thưởng ngoạn cảnh hoàng hôn phố thị."
    ),
    (
        "khach-san-rex", "historical", "Khách sạn Rex Saigon", 10.7758, 106.7008, 4,
        "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=800&q=80",
        "Khách sạn biểu tượng tại giao lộ Nguyễn Huệ - Lê Lợi, nơi diễn ra các cuộc họp báo Five O'Clock Follies lịch sử.",
        "Rex Saigon từng là garage ôtô hiện đại thời Pháp thuộc trước khi được chuyển đổi thành khách sạn xa hoa. Tầng thượng Rooftop Garden nhìn xuống toàn cảnh phố đi bộ Nguyễn Huệ và tòa đô chính đã đi vào ký ức của biết bao phóng viên quốc tế."
    ),
    (
        "thu-vien-khoa-hoc-tong-hop", "campus", "Thư viện Khoa học Tổng hợp TP.HCM", 10.7756, 106.6985, 4,
        "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&w=800&q=80",
        "Công trình thư viện kiến trúc hiện đại nhiệt đới xây dựng trên nền khám lớn Sài Gòn xưa.",
        "Tọa lạc trên đường Lý Tự Trọng, Thư viện Khoa học Tổng hợp khánh thành năm 1971 với các mảng lam chắn nắng bê tông hoa văn kỷ hà duyên dáng. Nơi đây là kho tàng tri thức đồ sộ lưu giữ hàng triệu đầu sách báo quý hiếm của phương Nam."
    ),
    (
        "toa-an-nhan-dan", "historical", "Tòa án Nhân dân TP. Hồ Chí Minh", 10.7748, 106.6946, 3,
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=800&q=80",
        "Di tích kiến trúc nghệ thuật cấp quốc gia xây dựng từ cuối thế kỷ 19 mang đậm phong cách tư pháp Pháp.",
        "Tòa án Thành phố khánh thành năm 1885 do kiến trúc sư Bourard thiết kế. Công trình nổi bật với hàng cột La Mã uy nghiêm, các bức tượng biểu tượng công lý và công viên cây xanh rợp bóng bao quanh."
    ),
    (
        "ngan-hang-nha-nuoc", "historical", "Ngân hàng Nhà nước Việt Nam (Chi nhánh TP.HCM)", 10.7708, 106.7042, 4,
        "https://images.unsplash.com/photo-1501167786227-4cba60f6d58f?auto=format&fit=crop&w=800&q=80",
        "Trụ sở Ngân hàng Đông Dương xưa mang phong cách kiến trúc Art Deco kết hợp họa tiết điêu khắc Chăm Pa.",
        "Tọa lạc bên bờ kênh Bến Nghé, tòa nhà hoàn thành năm 1930 với những thức cột bề thế và họa tiết thần điểu Garuda Chăm Pa đắp nổi công phu, tượng trưng cho uy lực tài chính và sự thịnh vượng vững bền."
    ),

    # --- Quận 5 & Khu Di sản Chợ Lớn (Văn hóa Hoa - Việt) ---
    (
        "sgu-main", "campus", "Trường Đại học Sài Gòn (SGU - Cơ sở chính)", 10.7591, 106.6823, 5,
        "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=800&q=80",
        "Ngôi trường đại học danh tiếng với tòa nhà cổ phong cách Pháp - Hoa hơn 100 năm tuổi trên đường An Dương Vương.",
        "Chào mừng bạn đến với Trường Đại học Sài Gòn (SGU). Tiền thân là trường Trung học Bác Ái xây dựng năm 1908, khuôn viên trường lưu giữ những dãy hành lang gạch đỏ vòm cong tuyệt mỹ, giao thoa giữa kiến trúc Tây âu và tinh thần Á Đông."
    ),
    (
        "chua-ba", "religious", "Chùa Bà Thiên Hậu (Tuệ Thành Hội Quán)", 10.7542, 106.6636, 5,
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
        "Ngôi miếu cổ linh thiêng bậc nhất Chợ Lớn xây dựng năm 1760 với những vòng nhang trầm cuộn tròn bảng lãng.",
        "Chùa Bà Thiên Hậu là trung tâm tín ngưỡng tâm linh lâu đời của cộng đồng người Hoa gốc Quảng Đông. Ngôi miếu nổi tiếng với quần thể gốm nung men xanh phù điêu tinh xảo trên bờ nóc và những khoanh nhang treo lơ lửng nguyện ước bình an."
    ),
    (
        "cho-lon", "market", "Chợ Bình Tây (Chợ Lớn)", 10.7498, 106.6514, 5,
        "https://images.unsplash.com/photo-1533900298318-6b8da08a523e?auto=format&fit=crop&w=800&q=80",
        "Ngôi chợ đầu mối sầm uất bậc nhất Nam Bộ do thương gia Quách Đàm hiến tặng xây dựng năm 1928.",
        "Chợ Bình Tây có kiến trúc bát giác độc đáo mái ngói âm dương nhiều tầng, tháp đồng hồ trung tâm và khoảng sân trời thoáng đãng. Đây là đầu mối buôn sỉ tấp nập cung ứng hàng hóa cho khắp các tỉnh miền Tây và cả nước."
    ),
    (
        "nghia-an", "religious", "Hội quán Nghĩa An (Chùa Ông)", 10.7531, 106.6619, 4,
        "https://images.unsplash.com/photo-1519817650390-64a93db51149?auto=format&fit=crop&w=800&q=80",
        "Nơi thờ phụng Quan Thánh Đế Quân của người Triều Châu với nghệ thuật điêu khắc gỗ thếp vàng lộng lẫy.",
        "Hội quán Nghĩa An là di tích kiến trúc nghệ thuật cấp quốc gia trên đường Nguyễn Trãi. Điểm đặc sắc nhất của chùa là các bức hoành phi, bao lam chạm trổ tinh vi mạ vàng rực rỡ và tượng ngựa Xích Thố oai phong nơi tiền điện."
    ),
    (
        "chua-ong-bon", "religious", "Chùa Ông Bổn (Nhị Phủ Miếu)", 10.7506, 106.6603, 4,
        "https://images.unsplash.com/photo-1509099836639-18ba1795216d?auto=format&fit=crop&w=800&q=80",
        "Di tích hơn 270 năm tuổi của cộng đồng người Hoa gốc Phúc Kiến thờ vị thần Phúc Đức Chánh Thần.",
        "Nhị Phủ Miếu khánh thành khoảng năm 1730, nổi bật với mái ngói hình thuyền uốn cong vút gắn phù điêu lưỡng long tranh châu bằng sành sứ. Không gian tĩnh mặc trầm mặc gợi nhớ thuở khai hoang lập nghiệp của tiền nhân."
    ),
    (
        "chua-on-lang", "religious", "Hội quán Ôn Lăng (Chùa Quan Âm)", 10.7535, 106.6631, 4,
        "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=800&q=80",
        "Ngôi chùa cổ của bang Tuyên Châu (Phúc Kiến) với tục 'đánh kẻ tiểu nhân' độc đáo vào dịp Tết Nguyên Tiêu.",
        "Hội quán Ôn Lăng thờ phụng Đức Mẹ Quan Âm và các vị thần bảo trợ dân gian. Kiến trúc chùa gây ấn tượng bởi những hàng cột gỗ quý chạm trổ chữ Nho và tục lệ 'đánh kẻ tiểu nhân' bằng giày dép để xua đuổi xui rủi đầu năm."
    ),
    (
        "nha-tho-cha-tam", "religious", "Nhà thờ Cha Tam", 10.7499, 106.6664, 4,
        "https://images.unsplash.com/photo-1543852786-1cf6624b9987?auto=format&fit=crop&w=800&q=80",
        "Thánh đường Công giáo độc nhất vô nhị pha trộn đường nét kiến trúc phương Tây và chùa miếu người Hoa.",
        "Nhà thờ Thánh Phanxicô Xaviê (thường gọi là Nhà thờ Cha Tam) hoàn thành năm 1902. Dù mang vóc dáng nhà thờ Gothic nhưng cổng vào lại thiết kế theo kiểu tam quan, nóc lợp ngói lưu ly và cột trụ chạm rồng đỏ son kiểu Trung Hoa."
    ),
    (
        "hao-si-phuong", "historical", "Hào Sĩ Phường (Trần Hưng Đạo B)", 10.7518, 106.6645, 4,
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80",
        "Con hẻm chung cư di sản hơn một thế kỷ mang đậm phong vị điện ảnh Hong Kong giữa lòng Quận 5.",
        "Hào Sĩ Phường gồm hai dãy nhà hai tầng đối diện nhau có ban công sắt chạy dài và cầu thang lộ thiên nối liền. Màu sơn vàng nhạt, bàn thờ Quan Công và nhịp sống chậm rãi khiến nơi đây tựa như một phim trường điện ảnh Hồng Kông thập niên 80."
    ),
    (
        "pho-dong-y", "historical", "Phố Đông y Hải Thượng Lãn Ông", 10.7505, 106.6620, 4,
        "https://images.unsplash.com/photo-1506368249639-73a05d6f6488?auto=format&fit=crop&w=800&q=80",
        "Con phố ngào ngạt hương thảo mộc đông y cổ truyền với hàng chục tiệm thuốc bắc hàng trăm năm tuổi.",
        "Bước chân vào đường Hải Thượng Lãn Ông, khứu giác của bạn sẽ được đánh thức bởi hương thơm thảo dược quế hồi ngào ngạt. Những tủ thuốc gỗ hàng trăm ngăn kéo cùng bàn tay bốc thuốc thoăn thoắt tạo nên di sản phi vật thể sống động."
    ),
    (
        "cho-an-dong", "market", "Chợ An Đông", 10.7564, 106.6698, 4,
        "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=800&q=80",
        "Trung tâm mua bán sỉ quần áo, giày dép và hàng khô cao cấp hàng đầu khu vực Chợ Lớn.",
        "Chợ An Đông hình thành từ thập niên 1950, hiện là trung tâm thương mại sầm uất nhiều tầng. Tầng trệt là thiên đường ẩm thực và hải vị sấy khô như vi cá, yến sào, trong khi các tầng trên tấp nập lái buôn thời trang từ khắp nơi hội tụ."
    ),
    (
        "cho-ray", "historical", "Bệnh viện Chợ Rẫy", 10.7574, 106.6598, 3,
        "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=800&q=80",
        "Bệnh viện đa khoa tuyến cuối lâu đời nhất phương Nam thành lập năm 1900 với tên gọi ban đầu Bệnh viện Bản xứ.",
        "Bệnh viện Chợ Rẫy ra đời trên vùng đất 'chợ rau rẫy' xưa của người Hoa. Trải qua hơn một thế kỷ phát triển, nơi đây là chiếc nôi y khoa danh tiếng và biểu tượng nhân ái, cứu chữa hàng triệu ca bệnh hiểm nghèo khắp miền Nam."
    ),
    (
        "cau-chu-y", "historical", "Cầu Chữ Y", 10.7528, 106.6775, 4,
        "https://images.unsplash.com/photo-1545671913-b89ac1b4ac10?auto=format&fit=crop&w=800&q=80",
        "Cây cầu ba nhánh hình chữ Y kỳ vĩ nối liền Quận 5 và Quận 8, ghi dấu trận đánh vang dội năm 1968.",
        "Cầu Chữ Y khánh thành năm 1941, có thiết kế phân thành ba nhánh bắc qua kênh Tàu Hủ và kênh Bến Nghé. Cây cầu là một kỳ tích kỹ thuật giao thông thời thuộc địa và từng là chiến trường ác liệt trong chiến dịch Tết Mậu Thân."
    ),
    (
        "chua-phung-son", "religious", "Chùa Phụng Sơn (Chùa Gò)", 10.7619, 106.6515, 4,
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
        "Di tích khảo cổ và danh lam cổ tự Phật giáo phái Lâm Tế xây trên phế tích văn hóa Óc Eo cổ đại.",
        "Tọa lạc trên một gò đất cao rợp bóng cổ thụ, Chùa Phụng Sơn xây dựng từ đầu thế kỷ 19. Các đợt khai quật khảo cổ tại đây đã phát hiện nhiều hiện vật bằng gốm và tượng Phật bằng đá thuộc nền văn hóa Óc Eo cách nay hơn ngàn năm."
    ),
    (
        "truong-le-hong-phong", "campus", "Trường THPT Chuyên Lê Hồng Phong", 10.7635, 106.6834, 4,
        "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=800&q=80",
        "Ngôi trường Petrus Ký danh tiếng lẫy lừng khánh thành năm 1928 với kiến trúc Art Deco uy nghi.",
        "Trường Petrus Ký (nay là THPT Chuyên Lê Hồng Phong) là cái nôi ươm mầm tinh hoa trí thức Việt Nam qua nhiều thời kỳ, từng ghi dấu ấn của các danh nhân như Giáo sư Trần Văn Giàu, nhạc sĩ Lưu Hữu Phước và Chủ tịch Nguyễn Minh Triết."
    ),
    (
        "chua-tam-son", "religious", "Chùa Tam Sơn (Hội quán Tam Sơn)", 10.7516, 106.6612, 3,
        "https://images.unsplash.com/photo-1519817650390-64a93db51149?auto=format&fit=crop&w=800&q=80",
        "Hội quán của người Hoa Phúc Kiến lập từ thời vua Minh Mạng, nổi tiếng cầu tự con cái linh ứng.",
        "Chùa Tam Sơn nằm trên đường Triệu Quang Phục, nổi bật với hệ thống khám thờ chạm trổ tinh vi bằng gỗ quý. Người dân Chợ Lớn thường đến đây thắp nhang kính bái bà Kim Huê Thánh Mẫu để cầu tự con cái bình an khỏe mạnh."
    ),
    (
        "cho-hoa-ho-thi-ky", "market", "Chợ hoa Hồ Thị Kỷ (Quận 10)", 10.7656, 106.6738, 4,
        "https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=800&q=80",
        "Chợ hoa tươi đầu mối lớn nhất thành phố và con phố ẩm thực đêm Campuchia độc đáo.",
        "Được mệnh danh là 'Tiểu Đà Lạt giữa lòng Sài Gòn', chợ hoa Hồ Thị Kỷ rực rỡ sắc màu thâu đêm suốt sáng với hàng trăm loài hoa tươi nhập về từ Đà Lạt và miền Tây. Con hẻm bên cạnh là phố ẩm thực Campuchia nức tiếng với chè Campuchia, bún num-bò-chóc."
    ),

    # --- Quận 3 & Phú Nhuận & Bình Thạnh (Di sản Văn hóa - Tâm linh) ---
    (
        "chua-vinh-nghiem", "religious", "Chùa Vĩnh Nghiêm", 10.7915, 106.6848, 5,
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
        "Tổ đình Phật giáo quy mô bề thế bên bờ kênh Nhiêu Lộc với tháp đá 7 tầng cao nhất Việt Nam.",
        "Khánh thành năm 1971, Chùa Vĩnh Nghiêm mang kiến trúc truyền thống chùa miền Bắc bằng bê tông cốt thép đầu tiên ở phía Nam. Ngôi tháp đá Quán Thế Âm 7 tầng sừng sững bên cầu Công Lý là điểm nhấn tâm linh nổi bật của tuyến kênh Nhiêu Lộc."
    ),
    (
        "chua-xa-loi", "religious", "Chùa Xá Lợi", 10.7788, 106.6882, 4,
        "https://images.unsplash.com/photo-1509099836639-18ba1795216d?auto=format&fit=crop&w=800&q=80",
        "Trung tâm Phật giáo lịch sử ghi dấu phong trào đấu tranh Phật giáo năm 1963.",
        "Chùa Xá Lợi xây dựng năm 1956 để tôn thờ xá lợi Phật Thích Ca. Tháp chuông 7 tầng cao 32 mét và tiếng đại hồng chung ngân vang là chứng nhân cho tinh thần bất khuất của Phật tử miền Nam trong cuộc đấu tranh bảo vệ chính pháp năm 1963."
    ),
    (
        "chua-ngoc-hoang", "religious", "Chùa Ngọc Hoàng (Phước Hải Tự)", 10.7919, 106.6976, 5,
        "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=800&q=80",
        "Ngôi chùa Đạo giáo cổ kính từng đón Tổng thống Mỹ Barack Obama viếng thăm năm 2016.",
        "Chùa Ngọc Hoàng xây dựng đầu thế kỷ 20 với mái ngói lưu ly rêu phong và hồ nuôi rùa phóng sinh thanh tịnh. Nơi đây nổi tiếng linh thiêng về cầu duyên và cầu tự, thu hút đông đảo phật tử và du khách quốc tế đến chiêm bái."
    ),
    (
        "lang-ong-ba-chieu", "historical", "Lăng Ông Bà Chiểu", 10.8016, 106.6961, 5,
        "https://images.unsplash.com/photo-1583417319070-4a69db38a482?auto=format&fit=crop&w=800&q=80",
        "Khu lăng mộ và đền thờ Tả quân Lê Văn Duyệt - danh tướng có công lớn mở mang vùng đất Gia Định.",
        "Lăng Ông Bà Chiểu là công trình kiến trúc cung đình lăng tẩm tiêu biểu của triều Nguyễn tại phương Nam. Lễ hội giỗ Tả quân hàng năm vào cuối tháng 7 âm lịch được công nhận là Di sản văn hóa phi vật thể quốc gia."
    ),
    (
        "chua-giac-lam", "religious", "Chùa Giác Lâm (Tổ đình Giác Lâm)", 10.7789, 106.6508, 5,
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
        "Ngôi chùa cổ nhất Thành phố Hồ Chí Minh xây dựng từ năm 1744 với kiến trúc chữ Tam độc đáo.",
        "Được xây dựng vào giữa thế kỷ 18, Chùa Giác Lâm bảo lưu gần như nguyên vẹn kiến trúc Phật giáo Nam Bộ xưa. Trong chùa hiện lưu giữ 113 pho tượng cổ bằng gỗ mít quý cùng tháp Xá Lợi 7 tầng lưu giữ xá lợi Phật linh thiêng."
    ),
    (
        "chua-phap-hoa", "religious", "Chùa Pháp Hoa (Quận 3)", 10.7909, 106.6833, 4,
        "https://images.unsplash.com/photo-1519817650390-64a93db51149?auto=format&fit=crop&w=800&q=80",
        "Ngôi chùa rực rỡ sắc màu bên dòng kênh Nhiêu Lộc, tâm điểm đại lễ thả hoa đăng Phật đản lung linh.",
        "Tọa lạc ngay khúc uốn đẹp nhất của kênh Nhiêu Lộc - Thị Nghè, Chùa Pháp Hoa nổi tiếng với đêm hội thả hoa đăng rực rỡ mỗi dịp Đại lễ Phật đản. Hàng ngàn ngọn đèn hoa đăng trôi trên dòng nước lung linh soi bóng ngôi bảo tháp uy nghiêm."
    ),
    (
        "truong-marie-curie", "campus", "Trường THPT Marie Curie", 10.7816, 106.6918, 4,
        "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=800&q=80",
        "Ngôi trường nữ sinh cổ kính xây dựng năm 1918 mang tên nhà nữ bác học đoạt hai giải Nobel.",
        "Trường Marie Curie là một trong những cơ sở giáo dục lâu đời và đẹp nhất Sài Gòn. Những tòa nhà cổ sơn màu vàng ấm, hàng cây cổ thụ xanh mát và những bức tượng bán thân nhà khoa học Marie Curie tạo nên không gian học đường đầy cảm hứng."
    ),
    (
        "kenh-nhieu-loc", "public-space", "Tuyến đường đi dạo Kênh Nhiêu Lộc - Thị Nghè", 10.7932, 106.6852, 4,
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80",
        "Dòng kênh hồi sinh kỳ diệu uốn lượn qua trung tâm thành phố với hàng liễu rủ và thuyền du ngoạn ngắm cảnh.",
        "Kênh Nhiêu Lộc là biểu tượng cho sức sống và sự chuyển mình của TP.HCM. Tuyến đường Hoàng Sa - Trường Sa rợp bóng hoa phượng và bằng lăng, đưa du khách đi thuyền ngắm nhìn những cây cầu lịch sử và các ngôi chùa cổ ven sông."
    ),
    (
        "cong-vien-le-van-tam", "public-space", "Công viên Lê Văn Tám", 10.7906, 106.6947, 3,
        "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=800&q=80",
        "Không gian xanh rợp bóng cây cổ thụ giữa Quận 1 và Quận 3, từng là nghĩa trang Mạc Đĩnh Chi xưa.",
        "Công viên Lê Văn Tám nổi bật với tượng đài người anh hùng thiếu niên và hàng cây cao vút. Nơi đây thường xuyên tổ chức Hội sách Thành phố hai năm một lần cùng các lễ hội ẩm thực quốc tế sôi động."
    ),
    (
        "nha-tho-huyen-sy", "religious", "Nhà thờ Huyện Sỹ", 10.7686, 106.6896, 4,
        "https://images.unsplash.com/photo-1543852786-1cf6624b9987?auto=format&fit=crop&w=800&q=80",
        "Nhà thờ cổ do ông bà Huyện Sỹ - ông ngoại Nam Phương Hoàng Hậu - hiến đất và tài chính xây dựng.",
        "Khánh thành năm 1905, Nhà thờ Chợ Đũi (Huyện Sỹ) xây dựng bằng đá hoa cương Biên Hòa kiên cố. Gian cung thánh là nơi yên nghỉ của ông bà Huyện Sỹ Lê Phát Đạt, một trong tứ đại phú hộ lừng danh Nam Kỳ lục tỉnh xưa."
    ),
    (
        "nha-tho-cho-quan", "religious", "Nhà thờ Chợ Quán", 10.7554, 106.6806, 4,
        "https://images.unsplash.com/photo-1548625361-195fe578772a?auto=format&fit=crop&w=800&q=80",
        "Giáo xứ cổ kính nhất tại TP.HCM với lịch sử hình thành từ năm 1722 bên bờ rạch Bến Nghé.",
        "Nhà thờ Chợ Quán là thánh đường có giáo xứ lâu đời nhất Sài Gòn. Ngôi thánh đường hiện tại xây dựng vào cuối thế kỷ 19 mang nét Gothic thanh thoát, với tháp chuông uy nghiêm ngân vang qua nhiều thế hệ giáo dân Quận 5."
    ),
    (
        "den-tran-hung-dao", "religious", "Đền thờ Đức Thánh Trần Hưng Đạo", 10.7937, 106.6941, 4,
        "https://images.unsplash.com/photo-1519817650390-64a93db51149?auto=format&fit=crop&w=800&q=80",
        "Đền thờ vị anh hùng dân tộc ba lần đại phá quân Nguyên Mông tọa lạc trên đường Võ Thị Sáu.",
        "Đền thờ Đức Thánh Trần Hưng Đạo được xây dựng trang nghiêm với các bức phù điêu chạm khắc các trận thủy chiến Bạch Đằng lừng lẫy. Hằng năm, đền tổ chức đại lễ kỷ niệm ngày giỗ Đức Thánh Trần thu hút đông đảo nhân dân thành kính dâng hương."
    ),
    (
        "den-mariamman", "religious", "Đền thờ Nữ thần Mariamman (Đền Bà Ấn)", 10.7729, 106.6967, 4,
        "https://images.unsplash.com/photo-1509099836639-18ba1795216d?auto=format&fit=crop&w=800&q=80",
        "Ngôi đền Hindu giáo rực rỡ với tháp gopuram nhiều tầng đắp nổi tượng các vị thần Ấn Độ.",
        "Tọa lạc trên đường Trương Định gần chợ Bến Thành, Đền thờ Nữ thần Mariamman xây dựng vào đầu thế kỷ 20 cho cộng đồng người Ấn. Người dân tin rằng áp trán vào bức tường đá linh thiêng phía sau đền sẽ nhận được sự che chở và may mắn."
    ),
    (
        "thanh-duong-hoi-giao", "religious", "Thánh đường Hồi giáo Jamia Al-Musulman", 10.7753, 106.7047, 4,
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
        "Thánh đường Hồi giáo trung tâm xây dựng từ năm 1935 với mái vòm trăng khuyết thanh tịnh trên đường Đông Du.",
        "Thánh đường Đông Du là trung tâm tôn giáo lớn của cộng đồng người theo đạo Hồi tại TP.HCM. Khuôn viên rợp bóng cây với hồ nước thanh tẩy và kiến trúc mái vòm hành lang mang lại cảm giác thanh thản, an yên giữa trung tâm hoa lệ."
    ),

    # --- Khu Landmark 81 & Bình Thạnh & Thủ Đức ---
    (
        "landmark-81", "historical", "Tòa nhà Landmark 81", 10.7951, 106.7218, 5,
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80",
        "Tòa nhà chọc trời cao nhất Việt Nam mô phỏng bó tre truyền thống kiêu hãnh vươn cao bên sông Sài Gòn.",
        "Với chiều cao 461.2 mét, Landmark 81 là kỳ tích kiến trúc hiện đại vươn tầm thế giới của Việt Nam. Tòa tháp lấy cảm hứng từ hình tượng bó tre đoàn kết, sở hữu đài quan sát Skyview ba tầng cao chót vót và trung tâm thương mại đẳng cấp."
    ),
    (
        "cong-vien-landmark", "public-space", "Công viên Central Park Vinhomes", 10.7938, 106.7245, 5,
        "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80",
        "Công viên ven sông quy mô 14 hecta tuyệt đẹp lấy cảm hứng từ Central Park New York danh tiếng.",
        "Công viên Central Park trải dài hơn 1km bờ sông Sài Gòn với những cây cầu đi bộ uốn lượn, vườn Nhật Bản hồ cá Koi và đài phun nước hoành tráng. Đây là điểm ngắm hoàng hôn và tòa tháp Landmark 81 ngoạn mục nhất thành phố."
    ),
    (
        "chua-buu-long", "religious", "Chùa Bửu Long (Chùa Xứ Chùa Vàng)", 10.8756, 106.8375, 5,
        "https://images.unsplash.com/photo-1569154941061-e231b4725ef1?auto=format&fit=crop&w=800&q=80",
        "Ngôi chùa Phật giáo Nam tông đẹp như cổ tích từng lọt top những ngôi chùa đẹp nhất thế giới.",
        "Tọa lạc trên đồi cao bên sông Đồng Nai, Chùa Bửu Long nổi tiếng với bảo tháp Gotama Cetiya màu trắng đỉnh chóp vàng lộng lẫy. Kiến trúc kết hợp tinh tế giữa phong cách Phật giáo nguyên thủy Thái Lan, Myanmar và văn hóa thời Nguyễn."
    ),
    (
        "chua-nam-thien", "religious", "Chùa Nam Thiên Nhất Trụ", 10.8525, 106.7588, 4,
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
        "Bản sao Chùa Một Cột Hà Nội uy nghiêm vươn lên giữa hồ Long Nhãn tại TP. Thủ Đức.",
        "Nam Thiên Nhất Trụ được Thượng tọa Thích Trí Dũng khởi công năm 1958 nhằm tái hiện hình ảnh Chùa Một Cột ngàn năm văn hiến nơi phương Nam. Đài hoa sen bằng bê tông vươn lên giữa hồ nước rực rỡ sắc hoa súng thanh tao."
    ),
    (
        "suoi-tien", "public-space", "Khu Du lịch Văn hóa Suối Tiên", 10.8654, 106.8025, 4,
        "https://images.unsplash.com/photo-1534567153574-2b12153a87f0?auto=format&fit=crop&w=800&q=80",
        "Công viên giải trí chuyên đề văn hóa lịch sử và thần thoại dân tộc đầu tiên tại Việt Nam.",
        "Suối Tiên nổi tiếng với biển nhân tạo Tiên Đồng - Ngọc Nữ và các đại cảnh kỳ vĩ phỏng theo thần thoại Lạc Long Quân - Âu Cơ, Sơn Tinh Thủy Tinh. Đây là điểm vui chơi giải trí gắn liền với tuổi thơ của hàng triệu du khách."
    ),
    (
        "dam-sen", "public-space", "Công viên Văn hóa Đầm Sen", 10.7686, 106.6385, 4,
        "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=800&q=80",
        "Tổ hợp vui chơi giải trí trên cạn và công viên nước khổng lồ quen thuộc của người dân Sài Gòn.",
        "Đầm Sen rộng hơn 50 hecta với hồ nước tự nhiên xanh biếc, vườn hoa, thủy cung và hàng chục trò chơi cảm giác mạnh. Vòng quay khổng lồ vươn cao trên bầu trời là điểm ngắm toàn cảnh Tây Nam thành phố tuyệt đẹp."
    ),
    (
        "cau-anh-sao", "public-space", "Cầu Ánh Sao (Starlight Bridge)", 10.7189, 106.7208, 5,
        "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=800&q=80",
        "Cây cầu đi bộ lung linh vắt qua hồ Bán Nguyệt với thác nước cầu vồng và đèn LED tựa dải ngân hà.",
        "Bắc qua rạch Thầy Tiêu tại khu đô thị Phú Mỹ Hưng Quận 7, Cầu Ánh Sao là biểu tượng hẹn hò lãng mạn. Mặt cầu gắn hệ thống đèn chiếu sáng mô phỏng các vì sao lấp lánh hòa cùng thác nước bảy sắc cầu vồng rực rỡ về đêm."
    ),
    (
        "ho-ban-nguyet", "public-space", "Hồ Bán Nguyệt & Phú Mỹ Hưng", 10.7198, 106.7186, 4,
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
        "Cung đường dạo bộ ven hồ hiện đại, lộng gió với chuỗi nhà hàng cà phê quốc tế phong cách resort.",
        "Khu vực Hồ Bán Nguyệt mang đến nhịp sống nghỉ dưỡng hiện đại giữa lòng đô thị. Những cung đường đi dạo uốn lượn bên rặng dừa nước và các trung tâm thương mại sầm uất là điểm dã ngoại cuối tuần lý tưởng cho mọi gia đình."
    ),
    (
        "dia-dao-cu-chi", "historical", "Khu Di tích Lịch sử Địa đạo Củ Chi (Bến Dược)", 11.1444, 106.4633, 5,
        "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=800&q=80",
        "Hệ thống địa đạo huyền thoại dài hơn 250km dưới lòng 'Đất thép thành đồng' kiên cường.",
        "Địa đạo Củ Chi là kỳ quan nghệ thuật quân sự độc nhất vô nhị. Mê cung đường hầm sâu trong lòng đất gồm nhiều tầng với bệnh viện dã chiến, bếp Hoàng Cầm, phòng hội họp tái hiện tinh thần bất khuất đánh giặc của quân dân miền Nam."
    ),
    (
        "chien-khu-rung-sac", "historical", "Khu Di tích Chiến khu Rừng Sác (Cần Giờ)", 10.5369, 106.8925, 4,
        "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=800&q=80",
        "Căn cứ thủy phi đội đặc công rừng ngập mặn Cần Giờ - Khu dự trữ sinh quyển thế giới.",
        "Rừng Sác Cần Giờ là chiến trường huyền thoại của Trung đoàn 10 Đặc công Rừng Sác. Nằm giữa rừng đước bạt ngàn của Khu dự trữ sinh quyển thế giới UNESCO, nơi đây tái hiện chân thực đời sống chiến đấu kiên cường giữa muôn trùng hiểm nguy."
    ),

    # --- Thêm các địa điểm văn hóa, học đường, chợ, ẩm thực nổi bật cho đủ 100 POIs ---
    (
        "truong-dh-khoa-hoc-tu-nhien", "campus", "Trường Đại học Khoa học Tự nhiên TP.HCM", 10.7631, 106.6822, 4,
        "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=800&q=80",
        "Cơ sở giáo dục đại học hàng đầu về khoa học cơ bản, tiền thân là Đại học Khoa học Sài Gòn.",
        "Nằm ngay trên đường Nguyễn Văn Cừ, trường là cái nôi đào tạo hàng vạn nhà khoa học, chuyên gia công nghệ và nhân tài phục vụ sự nghiệp phát triển đất nước qua nhiều thập kỷ."
    ),
    (
        "truong-dh-su-pham", "campus", "Trường Đại học Sư phạm TP.HCM", 10.7602, 106.6828, 4,
        "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=800&q=80",
        "Trường đại học trọng điểm quốc gia đào tạo đội ngũ giáo viên, nhà giáo dục xuất sắc cho miền Nam.",
        "Liền kề Đại học Sài Gòn, Đại học Sư phạm TP.HCM nổi tiếng với môi trường học thuật mẫu mực, giàu truyền thống sư phạm và là nơi gắn bó với tuổi thanh xuân của nhiều thế hệ thầy cô giáo."
    ),
    (
        "truong-dh-y-duoc", "campus", "Đại học Y Dược TP.HCM", 10.7558, 106.6601, 4,
        "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=800&q=80",
        "Trung tâm đào tạo nhân lực y tế hàng đầu phía Nam với bề dày lịch sử hơn 75 năm cống hiến.",
        "Đại học Y Dược TP.HCM trên đường Hồng Bàng là biểu tượng của tinh thần y đức, nơi tôi luyện những bác sĩ, dược sĩ tài năng, tận tụy chăm sóc sức khỏe cho nhân dân khắp mọi miền."
    ),
    (
        "truong-dh-bach-khoa", "campus", "Trường Đại học Bách Khoa TP.HCM (Cơ sở Lý Thường Kiệt)", 10.7725, 106.6578, 4,
        "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=800&q=80",
        "Đầu tàu đào tạo kỹ sư công nghệ và kỹ thuật hàng đầu Việt Nam thuộc Đại học Quốc gia TP.HCM.",
        "Tiền thân là Trung tâm Kỹ thuật Quốc gia Phú Thọ thành lập năm 1957, Đại học Bách Khoa TP.HCM là cái nôi sản sinh những sáng tạo công nghệ, công trình kỹ thuật mang tầm vóc quốc gia."
    ),
    (
        "nha-thi-dau-phu-tho", "public-space", "Nhà thi đấu Thể dục Thể thao Phú Thọ", 10.7695, 106.6565, 3,
        "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=800&q=80",
        "Khu phức hợp thể thao đa năng quy mô lớn, địa điểm đăng cai các đại hội thể thao và triển lãm quốc tế.",
        "Nhà thi đấu Phú Thọ khánh thành phục vụ SEA Games 22 với khán đài hiện đại sức chứa hàng ngàn người, thường xuyên diễn ra các trận cầu đỉnh cao, hội chợ triển lãm và đại nhạc hội cuồng nhiệt."
    ),
    (
        "san-van-dong-thong-nhat", "public-space", "Sân vận động Thống Nhất", 10.7589, 106.6598, 3,
        "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=800&q=80",
        "Thánh địa bóng đá lịch sử của Sài Gòn từ thập niên 1930 với những trận cầu rực lửa đam mê.",
        "Sân Thống Nhất là chứng nhân cho những thăng trầm của bóng đá nước nhà. Tiếng hò reo vang dội trên các khán đài bốn phương đã thắp sáng tình yêu thể thao nồng nhiệt của người dân Sài Gòn qua nhiều thập niên."
    ),
    (
        "ben-xe-mien-tay", "public-space", "Bến xe Miền Tây", 10.7388, 106.6185, 3,
        "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=800&q=80",
        "Cửa ngõ giao thông huyết mạch kết nối TP.HCM với 13 tỉnh thành Đồng bằng Sông Cửu Long.",
        "Bến xe Miền Tây tại quận Bình Tân là điểm khởi hành quen thuộc đưa hàng chục ngàn lượt hành khách mỗi ngày xuôi về miền Tây sông nước chở đầy tình quê ấm áp."
    ),
    (
        "cho-kim-bien", "market", "Chợ Kim Biên", 10.7512, 106.6562, 3,
        "https://images.unsplash.com/photo-1533900298318-6b8da08a523e?auto=format&fit=crop&w=800&q=80",
        "Khu chợ đầu mối chuyên doanh hương liệu, phụ liệu cơ khí và đồ gia dụng phong phú tại Quận 5.",
        "Nằm cận kề chợ Lớn, chợ Kim Biên nổi tiếng từ lâu như một trung tâm cung ứng linh kiện, hóa chất thực phẩm và đồ gia dụng đa dạng đáp ứng nhu cầu sản xuất của toàn vùng."
    ),
    (
        "cho-soai-kinh-lam", "market", "Chợ vải Soái Kình Lâm (Thương xá Đồng Khánh)", 10.7523, 106.6582, 4,
        "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=800&q=80",
        "Thiên đường chợ sỉ vải vóc lớn nhất nước với muôn vàn chất liệu lụa là, gấm vóc rực rỡ.",
        "Soái Kình Lâm là ngôi chợ chuyên doanh vải sỉ lớn nhất Việt Nam. Những cuộn vải gấm, lụa tơ tằm, ren thêu cao ngất xếp tầng tầng lớp lớp tạo nên một biển màu sắc sống động khó quên."
    ),
    (
        "ben-binh-dong", "historical", "Bến Bình Đông (Quận 8)", 10.7425, 106.6548, 5,
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
        "Bến sông thương hồ cổ kính với lễ hội chợ hoa xuân 'Trên bến dưới thuyền' đặc trưng Nam Bộ.",
        "Bến Bình Đông lưu giữ trọn vẹn nét văn hóa sông nước miệt vườn giữa lòng đô thị. Mỗi độ Tết đến xuân về, hàng trăm ghe thuyền chở đầy mai vàng, cúc mâm xôi tấp nập cập bến tạo nên bức tranh xuân mê đắm lòng người."
    ),
    (
        "hem-xom-chieu", "market", "Phố ẩm thực Hẻm 200 Xóm Chiếu (Quận 4)", 10.7612, 106.7045, 4,
        "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
        "Thánh địa ăn vặt nức tiếng đất Sài thành với hàng trăm món ngon đậm đà giá bình dân.",
        "Hẻm 200 đường Xóm Chiếu được ví như thiên đường ẩm thực đường phố của Quận 4. Từ phá lấu bò nghi ngút khói, ốc xào me chua ngọt đến bánh tráng nướng giòn rụm luôn sẵn sàng chiều lòng mọi thực khách sành ăn."
    ),
    (
        "cho-xom-chieu", "market", "Chợ Xóm Chiếu (Quận 4)", 10.7618, 106.7072, 3,
        "https://images.unsplash.com/photo-1533900298318-6b8da08a523e?auto=format&fit=crop&w=800&q=80",
        "Chợ truyền thống lâu đời gắn liền với làng nghề dệt chiếu lát ven sông Sài Gòn thế kỷ trước.",
        "Tên gọi Xóm Chiếu bắt nguồn từ xóm nghề dệt chiếu cói truyền thống thời xưa. Chợ ngày nay là khu chợ dân sinh trù phú với nguồn hải sản tươi rói và các sạp chè thạch mát lành."
    ),
    (
        "dinh-thong-tay-hoi", "historical", "Đình Thông Tây Hội (Gò Vấp)", 10.8358, 106.6662, 4,
        "https://images.unsplash.com/photo-1583417319070-4a69db38a482?auto=format&fit=crop&w=800&q=80",
        "Ngôi đình làng cổ kính nhất vùng đất Gia Định xưa được xây dựng từ năm 1679.",
        "Đình Thông Tây Hội là di tích kiến trúc nghệ thuật cấp quốc gia có tuổi đời hơn 340 năm. Bộ khung gỗ lim vững chãi và các bao lam chạm khắc tứ linh tinh xảo là bằng chứng quý giá về thuở mở đất của tiền nhân phương Nam."
    ),
    (
        "tu-vien-khanh-an", "religious", "Tu viện Khánh An (Quận 12)", 10.8682, 106.6875, 4,
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
        "Ngôi tự viện cổ kính mang phong cách Phật giáo Bắc truyền giao hòa phong vị kiến trúc Á Đông thanh thoát.",
        "Tu viện Khánh An nổi bật với tông màu nâu trầm của gỗ kết hợp màu đỏ son và hệ thống đèn lồng gỗ thanh tao. Không gian tĩnh lặng như chốn thiền môn thanh tịnh là điểm hành hương và thưởng ngoạn thanh bình."
    ),
    (
        "chua-ky-quang-2", "religious", "Chùa Kỳ Quang 2 (Gò Vấp)", 10.8425, 106.6812, 3,
        "https://images.unsplash.com/photo-1509099836639-18ba1795216d?auto=format&fit=crop&w=800&q=80",
        "Ngôi chùa đặc biệt '5 không' với kiến trúc hang đá độc đáo và mái ấm nuôi dưỡng trẻ mồ côi khuyết tật.",
        "Chùa Kỳ Quang 2 nổi tiếng với kiến trúc 'không cột, không tường, không cửa, không khóa, không xà' tựa như những hang đá thiên nhiên kỳ bí. Nơi đây còn là mái ấm nhân từ cưu mang hàng trăm mảnh đời cơ nhỡ suốt nhiều năm qua."
    ),
    (
        "thanh-that-sai-gon", "religious", "Thánh thất Sài Gòn (Đạo Cao Đài)", 10.7618, 106.6854, 4,
        "https://images.unsplash.com/photo-1519817650390-64a93db51149?auto=format&fit=crop&w=800&q=80",
        "Thánh thất tôn giáo Cao Đài uy nghiêm với biểu tượng Thiên Nhãn tỏa sáng trên đường Trần Hưng Đạo.",
        "Thánh thất Sài Gòn mang nét kiến trúc đặc trưng của đạo Cao Đài với hai tháp chuông trống vươn cao và ngọn Nghinh Phong Đài. Biểu tượng Thiên Nhãn (Mắt Trời) thể hiện tinh thần đại đồng tôn giáo và hướng thiện bao dung."
    ),
    (
        "bao-tang-phu-nu", "museum", "Bảo tàng Phụ nữ Nam Bộ", 10.7845, 106.6885, 4,
        "https://images.unsplash.com/photo-1544967082-d9d25d867d66?auto=format&fit=crop&w=800&q=80",
        "Nơi tôn vinh truyền thống anh hùng, bất khuất, trung hậu, đảm đang của phụ nữ miền Nam.",
        "Bảo tàng Phụ nữ Nam Bộ lưu giữ hàng vạn tư liệu hiện vật quý về trang phục áo dài truyền thống, nghề dệt khăn rằn và những chiến công oanh liệt của đội quân tóc dài trong sự nghiệp giải phóng dân tộc."
    ),
    (
        "bao-tang-tphcm", "museum", "Bảo tàng Thành phố Hồ Chí Minh (Dinh Gia Long)", 10.7761, 106.6995, 4,
        "https://images.unsplash.com/photo-1565034946487-077786996e27?auto=format&fit=crop&w=800&q=80",
        "Tòa dinh thự kiến trúc Tân cổ điển Pháp lộng lẫy trên đường Lý Tự Trọng với hệ thống địa đạo bí mật.",
        "Xây dựng năm 1890, tòa dinh thự mang phong cách Phục Hưng với cầu thang đôi uốn lượn tuyệt mỹ và mái vòm Baroque đài các. Tầng hầm của bảo tàng nối liền hệ thống địa đạo bí mật kiên cố từng được các nguyên thủ sử dụng."
    ),
    (
        "chua-hoang-phap", "religious", "Chùa Hoằng Pháp (Hóc Môn)", 10.8925, 106.5875, 4,
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
        "Trung tâm hoằng pháp và tu học Phật giáo nổi tiếng với các khóa tu mùa hè quy tụ hàng vạn Phật tử.",
        "Chùa Hoằng Pháp tọa lạc giữa khuôn viên thanh tịnh rợp bóng cây xanh tại Hóc Môn. Ngôi chùa là chiếc nôi của phong trào tu Phật thất và các hoạt động thiện nguyện, hoằng dương chính pháp rộng khắp cả nước."
    ),
    (
        "den-hung-thao-cam-vien", "historical", "Đền Hùng Thảo Cầm Viên", 10.7878, 106.7042, 3,
        "https://images.unsplash.com/photo-1583417319070-4a69db38a482?auto=format&fit=crop&w=800&q=80",
        "Ngôi đền mang kiến trúc đền miếu triều Nguyễn thờ phụng Quốc Tổ Hùng Vương giữa lòng công viên bách thảo.",
        "Khánh thành năm 1926 với tên gọi Đền Kỷ Niệm, ngôi đền có mái ngói vút cong chạm rồng phượng tinh tế. Hằng năm vào mùng 10 tháng 3 âm lịch, lễ giỗ Quốc Tổ Hùng Vương được tổ chức trọng thể tại đây với nghi thức dâng hương thiêng liêng."
    ),
    (
        "khu-do-thi-sala", "public-space", "Công viên Sala Thủ Thiêm", 10.7688, 106.7195, 4,
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
        "Không gian sinh thái ngập nước hiện đại với đài ngắm hoa sala khổng lồ phát sáng lộng lẫy về đêm.",
        "Công viên Sala nằm trong khu đô thị mới Thủ Thiêm, nổi bật với đài quan sát tạo hình bông hoa sala khổng lồ vươn lên giữa hồ nước sinh thái. Đây là điểm dạo mát ngắm hoàng hôn và skyline quận 1 tuyệt đẹp."
    ),
    (
        "cau-thu-thiem-1", "historical", "Cầu Thủ Thiêm", 10.7892, 106.7165, 3,
        "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80",
        "Cây cầu bê tông vượt sông Sài Gòn đầu tiên nối Quận Bình Thạnh với khu đô thị mới Thủ Thiêm.",
        "Thông xe năm 2007, Cầu Thủ Thiêm đánh dấu bước chuyển mình mở ra giai đoạn đánh thức tiềm năng bán đảo Thủ Thiêm. Từ trên cầu, du khách có thể phóng tầm mắt bao trọn tòa Landmark 81 và khúc sông uốn lượn thanh bình."
    ),
    (
        "nha-thieu-nhi-tphcm", "campus", "Nhà Thiếu nhi Thành phố Hồ Chí Minh", 10.7831, 106.6912, 3,
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80",
        "Cung văn hóa thiếu nhi mang hình tượng con thuyền vươn khơi ước mơ của tuổi thơ thành phố.",
        "Tọa lạc trên đường Nam Kỳ Khởi Nghĩa, Nhà Thiếu nhi Thành phố với tòa nhà mới mô phỏng con tàu bay tương lai là trung tâm sinh hoạt nghệ thuật, thể thao và sáng tạo khoa học của hàng triệu thanh thiếu nhi TP.HCM."
    ),
    (
        "cho-dan-sinh", "market", "Chợ Dân Sinh", 10.7668, 106.6965, 3,
        "https://images.unsplash.com/photo-1533900298318-6b8da08a523e?auto=format&fit=crop&w=800&q=80",
        "Ngôi chợ đồ cũ, kỷ vật chiến tranh và phụ tùng cơ khí độc nhất vô nhị ở trung tâm Sài Gòn.",
        "Chợ Dân Sinh hình thành từ thập niên 1950, nức tiếng là nơi săn lùng các món đồ cổ, bật lửa Zippo, la bàn quân đội và đồ phượt dã ngoại với phong vị phong trần độc đáo."
    ),
    (
        "cho-cu-ton-that-dam", "market", "Chợ Cũ Tôn Thất Đạm", 10.7715, 106.7031, 3,
        "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
        "Khu chợ nhỏ cổ kính nằm nép mình dưới chân các cao ốc chọc trời Quận 1, nổi tiếng ẩm thực gia truyền.",
        "Chợ Cũ Tôn Thất Đạm là một nét hoài niệm giữa lòng quận 1 hiện đại. Con phố ẩm thực ngắn nhưng đầy ắp các món ngon truyền thống như cháo lòng, hủ tiếu mì người Hoa và bánh mì kẹp đậm chất Sài Gòn xưa."
    ),
    (
        "ben-thuy-saigon-waterbus", "public-space", "Bến Tàu Thủy Bình An (Thủ Đức)", 10.7852, 106.7265, 3,
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
        "Ga tàu thủy thơ mộng đối diện tòa nhà Landmark 81, điểm dừng chân ngắm cảnh trên sông lý tưởng.",
        "Nằm bên bờ sông Thủ Đức, Ga Bình An là điểm dừng chân nổi tiếng trên tuyến Saigon Waterbus. Quán cà phê bờ sông tại đây mở ra góc nhìn toàn cảnh về phía cụm cao ốc Landmark 81 phản chiếu trên mặt nước sông Sài Gòn êm đềm."
    ),
    (
        "chua-vinh-trang-sg", "religious", "Chùa Vĩnh Phước (Quận 12)", 10.8415, 106.6482, 3,
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
        "Cổ tự thanh tịnh nép mình bên dòng kênh rợp bóng dừa nước, nơi bảo lưu nét thiền môn thanh thản.",
        "Chùa Vĩnh Phước là chốn tu tập thanh tịnh dành cho phật tử địa phương với vườn cây ăn trái sum suê, tiếng chuông chùa ngân nga sớm chiều xua tan đi những ồn ào náo nhiệt của phố thị."
    ),
    (
        "lang-hoa-go-vap", "market", "Công viên Làng Hoa Gò Vấp", 10.8435, 106.6575, 3,
        "https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=800&q=80",
        "Vùng đất lưu giữ ký ức làng hoa kiểng truyền thống lừng danh xứ Gò Vấp trăm năm trước.",
        "Làng hoa Gò Vấp từng là vựa hoa kiểng cung ứng cho khắp Nam Kỳ lục tỉnh. Ngày nay, công viên Làng Hoa là không gian sinh hoạt văn hóa, thể thao trong lành của đông đảo người dân quận Gò Vấp."
    ),
    (
        "cho-ba-chieu", "market", "Chợ Bà Chiểu (Bình Thạnh)", 10.8005, 106.6978, 4,
        "https://images.unsplash.com/photo-1533900298318-6b8da08a523e?auto=format&fit=crop&w=800&q=80",
        "Ngôi chợ bán lẻ sầm uất bậc nhất phía Đông thành phố, nức tiếng với món xôi gà xá xíu Bà Chiểu huyền thoại.",
        "Chợ Bà Chiểu xây dựng từ giữa thế kỷ 20, nổi tiếng là thiên đường ẩm thực đêm với món xôi gà xá xíu cay nồng gói lá chuối, chè mâm đủ vị và khu chợ đồ si đa dạng."
    ),
    (
        "cau-binh-loi", "historical", "Cầu Bình Lợi cổ", 10.8228, 106.7085, 3,
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80",
        "Cây cầu đường sắt vượt sông Sài Gòn đầu tiên hoàn thành năm 1902 với nhịp quay độc đáo cho tàu bè qua lại.",
        "Cầu đường sắt Bình Lợi hơn 115 năm tuổi từng có nhịp cầu quay ở giữa cho tàu bè đi qua sông Sài Gòn. Ngày nay, một phần nhịp cầu quay lịch sử được giữ lại làm di tích bảo tồn kỹ thuật cơ khí thuộc địa."
    ),
    (
        "san-bay-tan-son-nhat", "public-space", "Cảng Hàng không Quốc tế Tân Sơn Nhất", 10.8185, 106.6588, 5,
        "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=800&q=80",
        "Cửa ngõ hàng không quốc tế bận rộn và lâu đời nhất Việt Nam xây dựng từ những năm 1930.",
        "Sân bay Tân Sơn Nhất là đầu mối giao thông hàng không lớn nhất cả nước kết nối TP.HCM với năm châu bốn biển. Nơi đây chứng kiến dòng chảy giao thương, du lịch sôi động và những cuộc hội ngộ, chia tay đầy cảm xúc."
    ),
    (
        "cong-vien-gia-dinh", "public-space", "Công viên Gia Định", 10.8162, 106.6742, 4,
        "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=800&q=80",
        "Lá phổi xanh rộng lớn gần sân bay với khu vui chơi trẻ em và rạp xiếc nghệ thuật thành phố.",
        "Với diện tích cây xanh rộng gần 6 hecta, Công viên Gia Định sở hữu những thảm cỏ xanh mướt và hàng sọ khỉ rợp bóng. Nơi đây là điểm dã ngoại cuối tuần quen thuộc và là điểm đặt Rạp xiếc Thành phố Hồ Chí Minh."
    ),
    (
        "chua-phat-co-don", "religious", "Chùa Phật Cô Đơn (Bát Bửu Phật Đài - Bình Chánh)", 10.7788, 106.5185, 4,
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
        "Pho tượng Phật Thích Ca kỳ vĩ uy nghiêm nguyên vẹn giữa bom đạn chiến tranh khốc liệt tại Bình Chánh.",
        "Bát Bửu Phật Đài nổi tiếng với pho tượng Phật Thích Ca lộ thiên cao gần 5 mét. Dù trải qua mưa bom bão đạn trong chiến tranh, tượng Phật vẫn sừng sững bình an giữa rừng bạch đàn, trở thành điểm tựa tâm linh cầu an cầu duyên của muôn người."
    ),
    (
        "chua-van-hanh", "religious", "Thiền viện Vạn Hạnh (Phú Nhuận)", 10.7985, 106.6782, 3,
        "https://images.unsplash.com/photo-1519817650390-64a93db51149?auto=format&fit=crop&w=800&q=80",
        "Viện nghiên cứu Phật học và thiền viện thanh tịnh trên đường Nguyễn Văn Trỗi do Đại lão Hòa thượng Thích Minh Châu sáng lập.",
        "Thiền viện Vạn Hạnh là trung tâm nghiên cứu Phật học và dịch thuật Tam Tạng kinh điển danh tiếng. Không gian thiền môn thanh nhã, giản dị là nơi tìm về của những tâm hồn khao khát trí tuệ và sự an lạc nội tâm."
    ),
    (
        "chua-khanh-van-nam-vien", "religious", "Khánh Vân Nam Viện (Quận 11)", 10.7588, 106.6502, 4,
        "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=800&q=80",
        "Đạo quán Đạo giáo phái Toàn Chân duy nhất còn bảo tồn trọn vẹn tại miền Nam Việt Nam.",
        "Tọa lạc trên đường Nguyễn Thị Nhỏ, Khánh Vân Nam Viện thờ Lữ Tổ (Lữ Động Tân) theo truyền thống Đạo gia. Nơi đây còn có phòng thuốc nam từ thiện bốc thuốc cứu người nghèo suốt hơn nửa thế kỷ qua."
    ),
    (
        "pho-am-thuc-phan-xich-long", "market", "Khu phố ẩm thực Phan Xích Long (Phú Nhuận)", 10.7965, 106.6892, 4,
        "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
        "Tuyến phố ẩm thực nhộn nhịp bậc nhất quy tụ hàng trăm thương hiệu ăn uống và cà phê thịnh hành.",
        "Phan Xích Long được mệnh danh là 'thiên đường ăn uống' của quận Phú Nhuận. Con đường rực rỡ ánh đèn luôn đông nghẹt các bạn trẻ tụ họp thưởng thức từ trà sữa, lẩu nướng đến các món ăn đặc sản vùng miền."
    ),
    (
        "nha-hat-cai-luong-tran-huu-trang", "historical", "Nhà hát Cải lương Trần Hữu Trang", 10.7678, 106.6915, 3,
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=800&q=80",
        "Thánh đường nghệ thuật sân khấu Cải lương phương Nam mang tên soạn giả tài ba Trần Hữu Trang.",
        "Nhà hát là chiếc nôi bảo tồn và phát huy nghệ thuật đờn ca tài tử và sân khấu cải lương - Di sản văn hóa phi vật thể đại diện của nhân loại. Nơi đây từng thắp sáng tên tuổi của bao thế hệ nghệ sĩ cải lương tài danh."
    ),
    (
        "cau-phu-my", "historical", "Cầu Phú Mỹ", 10.7412, 106.7468, 4,
        "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80",
        "Cây cầu dây văng lớn nhất TP.HCM bắc qua sông Sài Gòn nối liền Quận 7 và Thành phố Thủ Đức.",
        "Khánh thành năm 2009, Cầu Phú Mỹ dài hơn 2km với hai trụ tháp hình chữ H vươn cao 145 mét. Cây cầu là tuyến vành đai huyết mạch rút ngắn khoảng cách lưu thông hàng hóa từ các cảng biển ra quốc lộ 1."
    ),
    (
        "den-tho-vua-hung-thu-duc", "historical", "Đền Tưởng niệm các Vua Hùng (TP. Thủ Đức)", 10.8688, 106.8425, 4,
        "https://images.unsplash.com/photo-1583417319070-4a69db38a482?auto=format&fit=crop&w=800&q=80",
        "Công trình đền thờ Quốc Tổ bề thế trên đồi cao thuộc Công viên Lịch sử Văn hóa Dân tộc.",
        "Đền tưởng niệm các vua Hùng tọa lạc trang nghiêm trên đỉnh đồi Vi Ba, lấy cảm hứng từ hình ảnh cánh chim Lạc và trống đồng Đông Sơn. Nơi đây là điểm hành hương hướng về cội nguồn dân tộc của đồng bào miền Nam."
    ),
    (
        "chua-chantarangsay", "religious", "Chùa Candaransi (Chùa Chantarangsay - Quận 3)", 10.7895, 106.6815, 4,
        "https://images.unsplash.com/photo-1569154941061-e231b4725ef1?auto=format&fit=crop&w=800&q=80",
        "Ngôi chùa Phật giáo Nam tông Khmer duy nhất rực rỡ sắc vàng giữa trung tâm Sài Gòn.",
        "Khánh thành năm 1946 bên bờ kênh Nhiêu Lộc, Chùa Chantarangsay (Ánh Trăng) mang đậm nét văn hóa kiến trúc Angkor Khmer với tượng rắn thần Naga, chim thần Krud và tháp thờ mạ vàng rực rỡ."
    ),
    (
        "cho-hoa-dam-sen", "market", "Chợ hoa Đầm Sen (Quận 11)", 10.7645, 106.6432, 3,
        "https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=800&q=80",
        "Khu chợ hoa tươi sỉ hoạt động hiện đại với hàng trăm chủng loại hoa nhập khẩu và trong nước.",
        "Cùng với Hồ Thị Kỷ, Chợ hoa Đầm Sen là đầu mối hoa tươi sầm uất bậc nhất của các nhà vườn Đà Lạt chuyển về TP.HCM lúc nửa đêm, tỏa đi khắp các tiệm hoa và sự kiện cưới hỏi trong vùng."
    ),
    (
        "nha-tho-ky-dong", "religious", "Nhà thờ Kỳ Đồng (Dòng Chúa Cứu Thế)", 10.7825, 106.6812, 4,
        "https://images.unsplash.com/photo-1543852786-1cf6624b9987?auto=format&fit=crop&w=800&q=80",
        "Trung tâm hành hương Kính Đức Mẹ Hằng Cứu Giúp nổi tiếng với các hoạt động bác ái nhân đạo xã hội.",
        "Nhà thờ Dòng Chúa Cứu Thế Kỳ Đồng khánh thành năm 1952 với kiến trúc hình chữ thập thoáng rộng. Nơi đây luôn mở rộng vòng tay đón nhận và hỗ trợ hàng ngàn hoàn cảnh khó khăn, thương binh và người nghèo cơ nhỡ."
    ),
    (
        "chua-vinh-phuoc-bt", "religious", "Chùa Diệu Pháp (Bình Thạnh)", 10.8256, 106.7025, 4,
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
        "Ngôi chùa thanh tịnh ven sông Sài Gòn nổi tiếng với hoạt động nuôi dưỡng người già neo đơn và phóng sinh cá.",
        "Nằm nép mình bên khúc sông Sài Gòn lộng gió ở Bình Thạnh, Chùa Diệu Pháp mang không gian thoát tục thanh bình. Mái ấm chùa Diệu Pháp là nơi che chở yêu thương cho hàng chục cụ già neo đơn không nơi nương tựa."
    ),
    (
        "cho-ba-hoa", "market", "Chợ Bà Hoa (Chợ ẩm thực Quảng Nam - Tân Bình)", 10.7895, 106.6525, 4,
        "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
        "Hồn quê xứ Quảng giữa lòng Sài Gòn với mì Quảng, bánh thuẫn, cá chuồn nướng nén thơm lừng.",
        "Chợ Bà Hoa (phường 11, Tân Bình) hình thành từ năm 1967 do bà Hoa lập nên cho đồng bào miền Trung di cư. Nơi đây là thiên đường của những người con xa quê muốn tìm lại hương vị đĩa mì Quảng cay nồng, bánh tráng đập mắm nêm đậm đà."
    ),
    (
        "bao-tang-art-in-paradise", "museum", "Bảo tàng Tranh 3D Art in Paradise (Quận 7)", 10.7485, 106.7042, 3,
        "https://images.unsplash.com/photo-1544967082-d9d25d867d66?auto=format&fit=crop&w=800&q=80",
        "Không gian nghệ thuật thị giác 3D tương tác sống động với hàng trăm bức bích họa đánh lừa thị giác.",
        "Rộng hơn 4.000m² với nhiều chủ đề đa dạng từ đại dương kỳ thú, thế giới hoang dã đến cổ tích thần tiên, Art in Paradise cho phép du khách trở thành một phần của tác phẩm nghệ thuật qua những góc chụp ảo diệu."
    ),
    (
        "ho-da-lang-dai-hoc", "public-space", "Hồ Đá Làng Đại học (TP. Thủ Đức)", 10.8812, 106.7825, 3,
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80",
        "Mặt hồ xanh biếc giữa hẻm đá tự nhiên, nơi ghi dấu ký ức thời sinh viên của bao thế hệ Đại học Quốc gia.",
        "Hồ Đá hình thành từ các mỏ khai thác đá xưa, có làn nước trong xanh phản chiếu vách đá dựng đứng. Dù mang vẻ đẹp hoang sơ kỳ thú nhưng nơi đây được bao bọc an toàn để sinh viên dạo mát ngắm hoàng hôn thanh bình."
    ),
    (
        "chua-phat-quang", "religious", "Chùa Phật Quang (Quận 10)", 10.7682, 106.6645, 3,
        "https://images.unsplash.com/photo-1519817650390-64a93db51149?auto=format&fit=crop&w=800&q=80",
        "Cổ tự thanh tịnh nổi bật với các chương trình thuyết giảng Phật pháp và lớp học tình thương cho trẻ nghèo.",
        "Chùa Phật Quang nằm sâu trong khu dân cư Quận 10 là điểm tựa tâm linh an lành. Tiếng chuông chùa thanh thoát sớm hôm nhắc nhở mỗi người gột rửa muộn phiền, nuôi dưỡng lòng từ bi và phụng sự cuộc đời."
    ),
    (
        "pho-di-bo-bach-dang", "public-space", "Cầu đi bộ Bến Bạch Đằng", 10.7725, 106.7068, 4,
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
        "Cung đường dạo bộ ven sông Sài Gòn lộng gió ngắm nhìn toàn cảnh trung tâm tài chính và tàu du lịch.",
        "Lối đi bộ lát gỗ và lan can kính hiện đại chạy dọc bến cảng là nơi đón những cơn gió trong lành từ sông lớn, mang lại không gian thư giãn tuyệt vời sau những giờ làm việc căng thẳng."
    ),
    (
        "cho-dau-moi-thu-duc", "market", "Chợ Đầu mối Nông sản Thủ Đức", 10.8655, 106.7325, 4,
        "https://images.unsplash.com/photo-1533900298318-6b8da08a523e?auto=format&fit=crop&w=800&q=80",
        "Chợ đầu mối hoa quả, nông sản lớn nhất miền Nam hoạt động nhộn nhịp từ nửa đêm về sáng.",
        "Mỗi đêm, hàng ngàn chuyến xe tải chở đầy rau củ trái cây từ Đà Lạt, miền Tây và miền Trung đổ về đây, tạo nên bức tranh lao động hối hả, cung cấp nguồn thực phẩm tươi ngon cho hơn 10 triệu cư dân thành phố."
    ),
    (
        "pha-cat-lai", "historical", "Bến phà Cát Lái", 10.7612, 106.7925, 3,
        "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=800&q=80",
        "Bến phà vượt sông Đồng Nai kết nối TP.HCM với vùng đất Nhơn Trạch thơ mộng.",
        "Bến phà Cát Lái là chuyến phà hoài niệm đưa hàng vạn lượt người và xe vượt sông mỗi ngày. Đứng trên boong phà lộng gió ngắm nhìn sóng nước mênh mông là trải nghiệm gắn liền với biết bao thế hệ người dân Đông Nam Bộ."
    ),
    (
        "sgu-co-so-2", "campus", "Trường Đại học Sài Gòn (Cơ sở 2 - Quận 8)", 10.7412, 106.6788, 3,
        "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=800&q=80",
        "Cơ sở đào tạo thực hành và nghiên cứu công nghệ hiện đại của Đại học Sài Gòn bên bờ kênh Đôi.",
        "Cơ sở 2 của SGU sở hữu các phòng thí nghiệm, xưởng thực hành công nghệ tiên tiến cùng khuôn viên xanh thoáng đãng, là nơi sinh viên các ngành kỹ thuật, mỹ thuật trau dồi tay nghề và phát triển dự án sáng tạo."
    ),
    (
        "sgu-co-so-3", "campus", "Trường Đại học Sài Gòn (Cơ sở 3 - Quận 3)", 10.7812, 106.6895, 3,
        "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=800&q=80",
        "Cơ sở đào tạo ngoại ngữ và bồi dưỡng cán bộ quản lý giáo dục uy tín của SGU tại trung tâm Quận 3.",
        "Tọa lạc trên đường Nguyễn Thông thanh bình, cơ sở 3 đóng vai trò quan trọng trong việc nâng cao năng lực ngoại ngữ và đào tạo chuyên sâu, là điểm đến quen thuộc của các học viên sau đại học và giáo viên thành phố."
    ),
]

print(f"Total POIs created: {len(POIS_DATA)}")

# 1. Generate backend/app/seed.py
seed_py_lines = [
    "from typing import Any",
    "",
    "",
    "def _poi(id: str, category: str, name: str, lat: float, lng: float, qr: str, priority: int = 3, image_url: str = '', description: str = '', narration_text: str = '') -> dict[str, Any]:",
    "    return {",
    "        'id': id,",
    "        'category': category,",
    "        'latitude': lat,",
    "        'longitude': lng,",
    "        'radius_m': 40,",
    "        'priority': priority,",
    "        'status': 'PUBLISHED',",
    "        'translation': {",
    "            'language_code': 'vi',",
    "            'name': name,",
    "            'description': description or f'{name} là một địa điểm văn hóa trong bộ sưu tập CityEcho quanh SGU.',",
    "            'narration_text': narration_text or f'Bạn đang khám phá {name}. Đây là một điểm dừng giàu câu chuyện trong hành trình CityEcho.',",
    "        },",
    "        'image_url': image_url or f'/images/pois/{id}.svg',",
    "        'audio_url': '',",
    "        'audio_duration_seconds': 0,",
    "        'qr_code': qr,",
    "    }",
    "",
    "",
    "SEED_POIS: dict[str, dict[str, Any]] = {",
]

LEGACY_QRS = {
    "cho-lon": "CITYECHO-BINHTAY",
    "sgu-main": "CITYECHO-SGU",
    "chua-ba": "CITYECHO-THIENHAU",
    "nha-tho-cha-tam": "CITYECHO-CHATAM",
    "nghia-an": "CITYECHO-NGHIAAN",
    "chua-ong-bon": "CITYECHO-ONGBON",
    "cho-an-dong": "CITYECHO-ANDONG",
    "cho-ray": "CITYECHO-CHORAY",
    "cau-chu-y": "CITYECHO-CHUY",
    "phung-son": "CITYECHO-PHUNGSON",
    "bao-tang-my-thuat": "CITYECHO-ARTMUSEUM",
    "ho-con-rua": "CITYECHO-HOCRUA",
}

for item in POIS_DATA:
    pid, cat, name, lat, lng, prio, img, desc, narr = item
    qr = LEGACY_QRS.get(pid, f"CITYECHO-{pid.replace('-', '').upper()[:10]}")
    name_escaped = name.replace("'", "\\'")
    desc_escaped = desc.replace("'", "\\'")
    narr_escaped = narr.replace("'", "\\'")
    seed_py_lines.append(
        f"    '{pid}': _poi('{pid}', '{cat}', '{name_escaped}', {lat}, {lng}, '{qr}', {prio}, '{img}', '{desc_escaped}', '{narr_escaped}'),"
    )

seed_py_lines.append("}\n")

with open("backend/app/seed.py", "w", encoding="utf-8") as f:
    f.write("\n".join(seed_py_lines))
print("Wrote backend/app/seed.py successfully!")

# 2. Generate frontend/src/samplePois.ts
sample_ts_lines = [
    'export type Status = "DRAFT" | "PENDING" | "NEEDS_REVISION" | "PUBLISHED" | "ARCHIVED";',
    'export type Poi = {',
    '  id: string;',
    '  category: string;',
    '  latitude: number;',
    '  longitude: number;',
    '  radius_m: number;',
    '  priority: number;',
    '  status: Status;',
    '  translation: { language_code?: string; name: string; description: string; narration_text: string };',
    '  image_url: string;',
    '  audio_url?: string;',
    '  audio_duration_seconds?: number;',
    '  qr_code: string;',
    '  distance_m?: number;',
    '};',
    '',
    'export const samplePois: Poi[] = [',
]

for item in POIS_DATA:
    pid, cat, name, lat, lng, prio, img, desc, narr = item
    qr = LEGACY_QRS.get(pid, f"CITYECHO-{pid.replace('-', '').upper()[:10]}")
    name_json = json.dumps(name, ensure_ascii=False)
    desc_json = json.dumps(desc, ensure_ascii=False)
    narr_json = json.dumps(narr, ensure_ascii=False)
    sample_ts_lines.append("  {")
    sample_ts_lines.append(f'    id: "{pid}",')
    sample_ts_lines.append(f'    category: "{cat}",')
    sample_ts_lines.append(f"    latitude: {lat},")
    sample_ts_lines.append(f"    longitude: {lng},")
    sample_ts_lines.append(f"    radius_m: 40,")
    sample_ts_lines.append(f"    priority: {prio},")
    sample_ts_lines.append('    status: "PUBLISHED",')
    sample_ts_lines.append(f'    qr_code: "{qr}",')
    sample_ts_lines.append(f'    image_url: "{img}",')
    sample_ts_lines.append(f"    translation: {{ language_code: 'vi', name: {name_json}, description: {desc_json}, narration_text: {narr_json} }},")
    sample_ts_lines.append("  },")

sample_ts_lines.extend([
    "];",
    "",
    'export function mediaUrl(api: string, url = "") {',
    '  if (!url) return "";',
    '  if (/^(https?:|data:|\\/images\\/)/.test(url)) return url;',
    '  return url.startsWith("/media") ? `${api}${url}` : url;',
    '}',
    "",
    'export function mapPinStyle(poi: Poi) {',
    '  return {',
    '    top: `${Math.min(Math.max(((10.79 - poi.latitude) / 0.045) * 80 + 8, 6), 88)}%`,',
    '    left: `${Math.min(Math.max(((poi.longitude - 106.645) / 0.06) * 80 + 8, 6), 88)}%`,',
    '  };',
    '}',
    "",
])

with open("frontend/src/samplePois.ts", "w", encoding="utf-8") as f:
    f.write("\n".join(sample_ts_lines))
print("Wrote frontend/src/samplePois.ts successfully!")

