document.addEventListener('DOMContentLoaded', () => {

    // 1. Smooth Scrolling cho các nút CTA có chứa link bắt đầu bằng #
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // 2. Xử lý logic Form Assessment Submit
    const assessmentForm = document.getElementById('assessmentForm');
    if (assessmentForm) {
        assessmentForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const assessmentSubmitBtn = document.getElementById('assessmentSubmitBtn');
            const assessmentLoader = document.getElementById('assessmentLoader');
            const assessmentSuccessMsg = document.getElementById('assessmentSuccessMsg');

            // Lấy dữ liệu từ form
            const formData = new FormData(assessmentForm);
            
            // Xử lý checkboxes - tập hợp tất cả các checkboxes được chọn cho mỗi câu hỏi
            const q3Values = Array.from(formData.getAll('question3'));
            const q4Values = Array.from(formData.getAll('question4'));
            const q5Values = Array.from(formData.getAll('question5'));

            // Kiểm tra ít nhất 1 lựa chọn cho mỗi nhóm checkbox
            if (q3Values.length === 0 || q4Values.length === 0 || q5Values.length === 0) {
                alert("Vui lòng chọn ít nhất một đáp án cho các câu hỏi trắc nghiệm!");
                return;
            }

            // Hiển thị UI loading
            if (assessmentSubmitBtn) assessmentSubmitBtn.parentElement.style.display = 'none';
            if (assessmentLoader) assessmentLoader.style.display = 'block';

            // Chuẩn bị dữ liệu gửi đi (Đã bỏ Câu 1, 2 bị lặp)
            const payload = {
                "Tên": formData.get('name'),
                "SĐT_Zalo": formData.get('phone'),
                "Câu 1 (Vấn đề)": q3Values.join(', '),
                "Câu 2 (Giải pháp đã thử)": q4Values.join(', '),
                "Câu 3 (Mục tiêu)": q5Values.join(', ')
            };

            // URL đích
            const scriptURL = 'https://script.google.com/macros/s/AKfycbweX7ojxQfDkdXB5rV5GukVEwz7OKhM_ZaBQZtkUd-KyA9FB4qkGiS37m-vpVta_v9LoQ/exec';
            
            // Gửi lên Google Sheet (no-cors: luôn resolve, không throw CORS error)
            fetch(scriptURL, {
                method: 'POST',
                mode: 'no-cors',
                headers: { 'Content-Type': 'text/plain' },
                body: JSON.stringify(payload)
            }).catch(() => {}); // Bỏ qua lỗi mạng nếu có

            // Luôn hiện thành công ngay sau khi gửi (no-cors không có response ý nghĩa)
            setTimeout(() => {
                if (assessmentLoader) assessmentLoader.style.display = 'none';
                assessmentForm.querySelector('.form-actions')?.remove();
                assessmentForm.querySelectorAll('.form-group, .form-row, .form-divider').forEach(el => el.style.display = 'none');
                
                const zaloBtn = document.getElementById('zaloAssessmentBtn');
                if (zaloBtn) zaloBtn.href = 'https://zalo.me/0877057918';

                if (assessmentSuccessMsg) assessmentSuccessMsg.style.display = 'block';
                console.log("Assessment submitted.");
            }, 1000);
        });
    }

    // 3. Xử lý logic Form Order Submit
    const orderForm = document.getElementById('orderForm');
    const submitBtn = document.getElementById('submitBtn');
    const loader = document.getElementById('loader');
    const paymentSection = document.getElementById('paymentSection');
    const finishBtn = document.getElementById('finishBtn');
    const qrImage = document.getElementById('qrImage');
    const transferContentText = document.getElementById('transferContentText');

    if (orderForm) {
        orderForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Ngăn chặn tải lại trang mặc định

            // Lấy dữ liệu từ form
            const formData = new FormData(orderForm);
            const data = Object.fromEntries(formData.entries());
            // Không tự động điền addInfo nữa để khách tự ghi cú pháp theo mẫu
            // Định dạng: https://img.vietqr.io/image/TÊN_NGÂN_HÀNG-STK-compact2.png?amount=SỐ_TIỀN&accountName=TÊN_CHỦ_TÀI_KHOẢN
            // Set QR code với số tiền cố định 99.000đ
            if (qrImage) {
                const qrUrl = `https://img.vietqr.io/image/MB-3530110082002-compact2.png?amount=99000&accountName=LE%20BAO%20MINH%20CHAU&addInfo=ebook%20${encodeURIComponent(data.phone)}`;
                qrImage.src = qrUrl;
            }

            // --- TÍCH HỢP GOOGLE APPS SCRIPT ---
            const scriptURL = 'https://script.google.com/macros/s/AKfycbweX7ojxQfDkdXB5rV5GukVEwz7OKhM_ZaBQZtkUd-KyA9FB4qkGiS37m-vpVta_v9LoQ/exec';

            // Hiển thị UI loading
            submitBtn.style.display = 'none';
            if (loader) loader.style.display = 'block';

            // Chuẩn bị dữ liệu gửi đi
            const payload = {
                name: data.fullname,
                phone: data.phone,
                email: data.email
            };

            // Gửi lên Google Sheet (no-cors: luôn resolve)
            fetch(scriptURL, {
                method: 'POST',
                mode: 'no-cors',
                headers: { 'Content-Type': 'text/plain' },
                body: JSON.stringify(payload)
            }).catch(() => {}); // Bỏ qua lỗi mạng nếu có

            // Luôn hiện QR sau 1 giây
            setTimeout(() => {
                if (loader) loader.style.display = 'none';
                orderForm.style.display = 'none';
                paymentSection.style.display = 'block';

                // Hiển thị nội dung chuyển khoản gợi ý với SĐT khách
                const transferDisplay = document.getElementById('transferContentDisplay');
                if (transferDisplay) {
                    transferDisplay.textContent = `ebook ${data.phone}`;
                }

                const zaloOrderBtn = document.getElementById('zaloOrderBtn');
                if (zaloOrderBtn) zaloOrderBtn.href = 'https://zalo.me/0877057918';

                console.log("Order submitted.");
            }, 1000);
        });
    }

    if (finishBtn) {
        finishBtn.addEventListener('click', () => {
            alert("Cảm ơn bạn! Chúng tôi đã ghi nhận và sẽ gửi Ebook qua Zalo cho bạn sớm nhất!");
            // Quay lại trạng thái ban đầu nếu cần
            paymentSection.style.display = 'none';
            orderForm.style.display = 'block';
            submitBtn.style.display = 'block';
            orderForm.reset();
        });
    }

    // --- CHATBOT LOGIC ---
    const chatbotBubble = document.getElementById('chatbotBubble');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const chatClose = document.getElementById('chatClose');
    const chatBody = document.getElementById('chatBody');
    const chatOptions = document.getElementById('chatOptions');
    const scrollUp = document.getElementById('scrollUp');
    const scrollDown = document.getElementById('scrollDown');

    const salesScript = {
        greeting: "Chào bạn nhé, mình là giảng viên đại học, năm nay mình 55 tuổi. Rất vui vì bạn đã ghé thăm và quan tâm đến hành trình chia sẻ này.\n\nBạn biết không, trước khi trở thành một người 'đi ngang qua' stress như hiện tại, mình cũng từng có lúc để bộ não của mình 'gồng' đến kiệt sức. Nếu bạn đang cảm thấy mệt mỏi, mất ngủ hay đơn giản là muốn tìm lại sự bình yên bên trong, thì bạn tìm đúng chỗ rồi đấy. Thử suy nghĩ xem, đã bao lâu rồi bạn chưa cho phép não bộ mình được 'nghỉ ngơi' thực sự?",
        faqs: [
            { q: "Phí 99k này là phí gì vậy chị?", a: "À, đây là một mức phí nho nhỏ mình đặt ra để chúng ta cùng có sự cam kết với nhau thôi. Bạn biết đấy, những thứ miễn phí thường bị mình lãng quên nhanh lắm. 99k — chỉ bằng hai ly cafe — nhưng nó là cái 'mỏ neo' để bạn nghiêm túc dành 5 ngày tới cho chính bản thân mình. Mình muốn tìm những người thực sự muốn thay đổi, bạn có đồng ý với mình không?" },
            { q: "Em không biết gì về khoa học thần kinh thì có học được không?", a: "Bạn đừng lo nhé! Mình làm giảng viên nên mình hiểu: kiến thức càng cao siêu thì càng phải nói sao cho dễ hiểu nhất. Ebook này không có từ ngữ hàn lâm đâu, toàn là những bài thực hành nhỏ xíu mà bạn có thể làm ngay khi đang ngồi làm việc hoặc trước khi đi ngủ. Mình đồng hành cùng bạn mà!" },
            { q: "Em bận lắm, ngày nào cũng làm khuya thì lấy đâu thời gian?", a: "Mình hiểu mà, vì mình cũng từng như thế. Nhưng bạn hãy hình dung xem: vì não mình 'kẹt xe' nên mình làm gì cũng chậm và mệt. Mỗi ngày trong hành trình này chỉ tốn của bạn khoảng 15-20 phút thôi. Việc bạn dành chút thời gian này thực chất là để giúp bạn làm việc hiệu quả hơn và có nhiều thời gian nghỉ ngơi hơn sau này đó." },
            { q: "5 ngày thì làm sao thay đổi được cả một bộ não?", a: "Hợp lý lắm! 5 ngày không phải phép màu để biến bạn thành người khác ngay lập tức. Nhưng 5 ngày là đủ để bạn 'nhận diện' được những tín hiệu cầu cứu của cơ thể mà bấy lâu nay bạn bỏ qua. Khi bạn biết cách 'tắt' chế độ báo động, não bạn sẽ bắt đầu tự chữa lành. Đó là sự khởi đầu của một vòng lặp mới, tích cực hơn." },
            { q: "Thanh toán xong bao lâu em nhận được Ebook?", a: "Ngay sau khi bạn gửi ảnh xác nhận chuyển khoản qua Zalo cho mình, mình hoặc các bạn hỗ trợ sẽ gửi link tải Ebook trực tiếp cho bạn luôn. Thường thì chỉ mất vài phút thôi nè. Nếu có trục trặc gì, mình vẫn ở đây hỗ trợ bạn 1:1 qua Zalo mà, cứ yên tâm nha." },
            { q: "Em tập thiền Yoga lâu rồi nhưng vẫn stress, cái này khác gì?", a: "Thiền và Yoga tuyệt lắm, mình cũng rất thích. Nhưng nếu ví cơ thể như một chiếc radio, thì Ebook này giúp bạn 'dò đúng đài'. Đôi khi mình thiền nhưng não vẫn 'gồng' vì mình chưa xử lý được cái gốc rễ của sự căng thẳng thần kinh. Khi bạn hiểu cơ chế não mình đang vận hành thế nào qua 5 ngày này, thì việc bạn thiền hay tập Yoga sau đó sẽ hiệu quả hơn gấp nhiều lần." },
            { q: "Em bị mất ngủ, tài liệu này có giúp ngủ ngon hơn không?", a: "Đây chính là 'điểm chạm' của Ngày thứ 2 trong hành trình đó bạn. Mình sẽ chia sẻ về 'Phím nguồn' để làm dịu não. Khi thần kinh phó giao cảm được kích hoạt đúng cách, cơ thể bạn sẽ tự hiểu là: 'À, an toàn rồi, ngủ thôi'. Nhiều bạn học viên của mình đã tìm lại được giấc ngủ ngon ngay sau bài học này đấy." },
            { q: "Em hay bị đau vai gáy với đau đầu, liên quan gì đến não không?", a: "Có chứ, liên quan mật thiết luôn! Khi não bạn căng thẳng, nó sẽ gửi tín hiệu bắt các cơ bắp phải co lại để bảo vệ cơ thể (chế độ chiến đấu). Đau vai gáy thường là dấu hiệu cho thấy bạn đang 'gồng' quá mức mà không biết. Trong Ebook, mình sẽ hướng dẫn bạn cách nhận diện 10 dấu hiệu này để bạn nới lỏng cơ thể ra nhé." },
            { q: "Đây là sách giấy hay sách điện tử vậy chị?", a: "Đây là Ebook (sách điện tử) định dạng PDF sắc nét nhé. Bạn có thể lưu vào điện thoại, máy tính để đọc bất cứ lúc nào. Mình chọn định dạng này để bạn có thể bắt đầu hành trình ngay lập tức mà không phải đợi ship sách cồng kềnh nè." },
            { q: "Chương trình này phù hợp với những ai nhất hả chị?", a: "Mình viết dành cho những 'người anh, người em' đang thấy mình mắc kẹt: sinh viên đang loay hoay, nhân viên văn phòng đang kiệt sức, hay freelancer đang bị quá tải. Nói chung là bất kỳ ai cảm thấy bên trong mình đang không ổn và muốn học cách yêu lấy chính mình thông qua góc nhìn khoa học nhưng đầy tình cảm." }
        ],
        closing: "Nếu bạn thấy mình trong những câu chuyện mình vừa kể, thì đừng ngần ngại nữa nhé. Chỉ 99.000đ để bắt đầu một hành trình mới cho bộ não và tâm trí của bạn.\n\nHãy hành động ngay hôm nay, vì cơ thể bạn đã đợi đủ lâu rồi. Nhấn nút đăng ký hoặc nhắn tin chuyển khoản cho mình luôn nhé, mình đợi để đồng hành cùng bạn!",
        hesitation: "Mình hiểu là đôi khi chúng ta cần thêm thời gian cân nhắc. Nếu bạn chưa sẵn sàng mua ngay, hay thử điền Bản đánh giá cá nhân phía trên nhé. Nó giúp bạn tự nhìn lại vấn đề của mình, hoàn toàn miễn phí và rất hữu ích đó!"
    };

    let isChatInit = false;

    function addMessage(text, sender = 'bot') {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-msg msg-${sender}`;
        msgDiv.innerText = text;
        chatBody.appendChild(msgDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    function showTyping() {
        const typing = document.createElement('div');
        typing.className = 'typing-indicator';
        typing.id = 'typing';
        typing.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
        chatBody.appendChild(typing);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    function removeTyping() {
        const typing = document.getElementById('typing');
        if (typing) typing.remove();
    }

    function updateArrows() {
        if (!scrollUp || !scrollDown) return;
        
        if (chatOptions.scrollTop <= 5) {
            scrollUp.classList.add('hidden');
        } else {
            scrollUp.classList.remove('hidden');
        }

        if (chatOptions.scrollTop + chatOptions.clientHeight >= chatOptions.scrollHeight - 5) {
            scrollDown.classList.add('hidden');
        } else {
            scrollDown.classList.remove('hidden');
        }
    }

    function renderOptions() {
        chatOptions.innerHTML = '';
        salesScript.faqs.forEach((faq, index) => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.innerText = faq.q;
            btn.onclick = () => handleFaqClick(index);
            chatOptions.appendChild(btn);
        });
        
        // Cập nhật mũi tên sau khi render
        setTimeout(updateArrows, 100);
    }

    function handleFaqClick(index) {
        const faq = salesScript.faqs[index];
        addMessage(faq.q, 'user');
        chatOptions.innerHTML = '';
        scrollUp.classList.add('hidden');
        scrollDown.classList.add('hidden');
        
        showTyping();
        setTimeout(() => {
            removeTyping();
            addMessage(faq.a, 'bot');
            
            // Show conversion buttons
            const actionContainer = document.createElement('div');
            actionContainer.className = 'action-btns';
            
            const buyBtn = document.createElement('button');
            buyBtn.className = 'btn btn-submit btn-small';
            buyBtn.innerText = 'Đăng ký nhận Ebook ngay';
            buyBtn.onclick = () => {
                chatbotWindow.classList.remove('active');
                document.getElementById('booking-form').scrollIntoView({ behavior: 'smooth' });
            };

            const backBtn = document.createElement('button');
            backBtn.className = 'option-btn btn-small';
            backBtn.innerText = 'Hỏi câu khác';
            backBtn.onclick = renderOptions;

            actionContainer.appendChild(buyBtn);
            actionContainer.appendChild(backBtn);
            chatBody.appendChild(actionContainer);
            chatBody.scrollTop = chatBody.scrollHeight;
        }, 1000);
    }

    function initChat() {
        if (isChatInit) return;
        isChatInit = true;
        chatBody.innerHTML = '';
        showTyping();
        setTimeout(() => {
            removeTyping();
            addMessage(salesScript.greeting, 'bot');
            renderOptions();
        }, 1500);
    }

    if (scrollUp && scrollDown) {
        scrollUp.addEventListener('click', () => {
            chatOptions.scrollBy({ top: -100, behavior: 'smooth' });
        });
        scrollDown.addEventListener('click', () => {
            chatOptions.scrollBy({ top: 100, behavior: 'smooth' });
        });
        chatOptions.addEventListener('scroll', updateArrows);
    }

    chatbotBubble.addEventListener('click', () => {
        chatbotWindow.classList.toggle('active');
        if (chatbotWindow.classList.contains('active')) {
            initChat();
            // Hide notification bulb
            const notif = document.querySelector('.bubble-notification');
            if (notif) notif.style.display = 'none';
        }
    });

    chatClose.addEventListener('click', () => {
        chatbotWindow.classList.remove('active');
    });
});
