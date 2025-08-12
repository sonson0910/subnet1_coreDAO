# Hướng Dẫn Dọn Dẹp Dự Án Subnet1 Aptos

## 🧹 Tổng Quan

Dự án này có rất nhiều file trùng lặp, backup files, và test files cũ có thể được dọn dẹp để làm gọn dự án. Tất cả các file quan trọng sẽ được bảo vệ trong quá trình dọn dẹp.

## 🛡️ Bảo Vệ File Quan Trọng

Các file sau đây sẽ **KHÔNG BAO GIỜ** bị xóa:
- `README.md` - Hướng dẫn dự án
- `.env` - Cấu hình môi trường
- `requirements.txt` - Dependencies
- `subnet1/` - Core subnet implementation
- `config/` - Cấu hình dự án
- `entities/` - Thông tin entities
- `scripts/` - Scripts chính
- `tests/` - Test files chính

## 🚀 Cách Sử Dụng

### 1. Dọn Dẹp Nhanh (Khuyến Nghị)

```bash
cd subnet1_aptos
python quick_cleanup.py
```

Script này sẽ:
- Loại bỏ các file trùng lặp rõ ràng (có số ở cuối)
- Loại bỏ backup files
- Loại bỏ log files
- Tạo backup trước khi xóa
- Bảo vệ tất cả file quan trọng

### 2. Dọn Dẹp Toàn Diện

```bash
cd subnet1_aptos
python cleanup_project.py --dry-run  # Xem trước những gì sẽ bị xóa
python cleanup_project.py             # Thực hiện dọn dẹp
```

### 3. Dọn Dẹp Với Thư Mục Cụ Thể

```bash
python cleanup_project.py --project-root /path/to/subnet1_aptos
```

## 📋 Các Loại File Sẽ Bị Xóa

### File Trùng Lặp
- `test_script_compatibility 2.py`
- `test_script_compatibility 3.py`
- `start_network_simple 2.py`
- `start_network_simple 3.py`
- `registration_summary 4.json`
- `metagraph_update_config 4.json`

### Backup Files
- `.env 2.backup_before_validator2`
- `.env 2.v2`
- `test_script_compatibility 2.py`
- `start_validators_debug 2.py`

### Log Files
- `miner2.log`
- `validator_state.json`

### Thư Mục Có Thể Dọn Dẹp
- `backup/` - Chứa các file backup cũ
- `fixes/` - Chứa các script fix tạm thời

## 🔍 Kiểm Tra Trước Khi Dọn Dẹp

### Dry Run (Chạy Thử)
```bash
python cleanup_project.py --dry-run
```

Điều này sẽ hiển thị tất cả file sẽ bị xóa mà không thực sự xóa chúng.

### Kiểm Tra Backup
Tất cả file bị xóa sẽ được backup vào:
- `cleanup_backup/` - Cho script chính
- `quick_cleanup_backup/` - Cho script nhanh

## 📊 Kết Quả Dọn Dẹp

Sau khi dọn dẹp, bạn sẽ thấy:
- Dự án gọn gàng hơn
- Ít file trùng lặp
- Cấu trúc thư mục rõ ràng hơn
- File `cleanup_summary.json` chứa thông tin chi tiết

## ⚠️ Lưu Ý Quan Trọng

1. **Luôn chạy dry-run trước** để xem những gì sẽ bị xóa
2. **Backup được tạo tự động** trước khi xóa bất kỳ file nào
3. **File quan trọng được bảo vệ** - không thể xóa nhầm
4. **Kiểm tra backup** sau khi dọn dẹp để đảm bảo an toàn

## 🆘 Khôi Phục File

Nếu cần khôi phục file nào đó:

```bash
# Tìm file trong backup
ls cleanup_backup/

# Khôi phục file cụ thể
cp cleanup_backup/path/to/file ./path/to/file

# Hoặc khôi phục toàn bộ thư mục
cp -r cleanup_backup/subdirectory ./
```

## 📞 Hỗ Trợ

Nếu gặp vấn đề trong quá trình dọn dẹp:
1. Kiểm tra file `cleanup_summary.json`
2. Xem log trong terminal
3. Kiểm tra thư mục backup
4. Khôi phục file từ backup nếu cần

## 🎯 Mục Tiêu Dọn Dẹp

- **Giảm 60-80%** số lượng file không cần thiết
- **Giữ nguyên 100%** chức năng dự án
- **Cải thiện** khả năng đọc và bảo trì code
- **Tối ưu hóa** cấu trúc thư mục
