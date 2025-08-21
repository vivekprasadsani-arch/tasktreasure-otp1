# Country File Management System - TaskTreasure OTP Bot

## 🌍 Overview

The TaskTreasure OTP Bot now includes a comprehensive country file management system that allows admins to upload, manage, and update phone number files for different countries directly through the Telegram bot.

## 📁 Features

### ✅ File Upload System
- **Direct Upload**: Upload Excel files through Telegram
- **Automatic Processing**: Validates and processes files automatically
- **File Replacement**: Replaces existing country files seamlessly
- **New Countries**: Add new countries by uploading files

### ✅ File Validation
- **Format Checking**: Ensures files are in Excel format (.xlsx/.xls)
- **Content Validation**: Verifies phone number format and quality
- **Quality Control**: Requires minimum 50% valid numbers
- **Column Detection**: Automatically detects phone number columns

### ✅ Country Management
- **List Countries**: View all available countries with statistics
- **Delete Countries**: Remove countries (with safety checks)
- **Reload System**: Refresh country list without restart
- **Backup System**: Automatic backups before file operations

## 🚀 How to Use

### 1. Upload New Country File

**Step 1: Prepare Excel File**
```
Column Name: number (or 'phone', 'mobile')
Format: International phone numbers

Example:
number
+21612345678
+21687654321
+21698765432
```

**Step 2: Upload via Bot**
1. Send `/upload` command to get instructions
2. Upload Excel file as document
3. Add country name as caption (e.g., "Tunisia")
4. Bot will validate and process automatically

**Step 3: Confirmation**
```
✅ Country Added Successfully!

🌍 Country: Tunisia
📊 Numbers: 1,250 valid numbers
📁 File: tunisia_numbers.xlsx
📈 Action: Added new country file

🔄 Status: Country is now available for users!
```

### 2. Update Existing Country

**Same Process as New Upload:**
- Upload file with existing country name
- Bot automatically replaces old file
- Creates backup of previous version
- Updates number tracking system

**Example:**
```
✅ Country Updated Successfully!

🌍 Country: Venezuela
📊 Numbers: 2,100 valid numbers
📁 File: venezuela_updated.xlsx
📈 Action: Updated existing country file

🔄 Status: Country is now available for users!
```

## 📋 Admin Commands

### Country Management Commands

| Command | Description | Usage Example |
|---------|-------------|---------------|
| `/upload` | Show upload instructions | `/upload` |
| `/countries` | List all countries with stats | `/countries` |
| `/delete_country <name>` | Delete a country file | `/delete_country Tunisia` |
| `/reload_countries` | Reload country list | `/reload_countries` |

### File Upload Process

**Direct Upload Method:**
1. Send Excel file as document
2. Add country name as caption
3. Bot processes automatically

**Command-Based Method:**
1. Use `/upload` for instructions
2. Follow guided upload process

## 📊 Country Statistics

### Viewing Country Information

Use `/countries` to see detailed information:

```
🌍 Available Countries (5):

1. 🇳🇪 Venezuela
   📊 Numbers: 2,100 total, 15 assigned
   📁 Size: 245.3 KB
   🕒 Updated: 2024-01-15 14:30
   📍 Index: 23

2. 🇳🇪 Tunisia
   📊 Numbers: 1,250 total, 8 assigned
   📁 Size: 156.7 KB
   🕒 Updated: 2024-01-15 12:15
   📍 Index: 12

Commands:
• /upload - Upload new country file
• /delete_country <name> - Delete country file
• /reload_countries - Reload country list
```

### Statistics Explained

- **Numbers**: Total numbers in file vs currently assigned
- **Size**: File size in KB
- **Updated**: Last modification time
- **Index**: Current position in number allocation

## 🔧 File Format Requirements

### Supported Formats
- **Excel Files**: .xlsx, .xls
- **CSV Support**: Coming in future updates

### Column Requirements
**Accepted Column Names:**
- `number` (preferred)
- `phone`
- `mobile`

**Phone Number Format:**
```
✅ Good Formats:
+21612345678
21612345678
+1-555-123-4567
+44 20 7123 4567

❌ Bad Formats:
123 (too short)
abc123def (letters)
+1234567890123456 (too long)
```

### File Validation Rules

1. **Minimum Numbers**: At least 1 valid number
2. **Success Rate**: Minimum 50% valid numbers
3. **Column Detection**: Must have recognizable phone column
4. **File Size**: Reasonable size limits (handled automatically)

## 🛡️ Safety Features

### Backup System
- **Automatic Backups**: Created before any file operation
- **Rollback Protection**: Can restore if upload fails
- **Deletion Backups**: Files backed up before deletion

### User Protection
- **Active User Check**: Cannot delete countries with active users
- **Validation**: Extensive file validation before processing
- **Error Recovery**: Automatic cleanup on failures

### Admin-Only Access
- **Permission Check**: Only configured admin can upload
- **Secure Processing**: Safe file handling and validation
- **Audit Logging**: All operations logged for security

## 🔄 File Processing Workflow

### Upload Process
```
1. File Upload → 2. Format Check → 3. Content Validation
         ↓              ↓                   ↓
4. Backup Creation → 5. File Processing → 6. System Update
         ↓              ↓                   ↓
7. Success Notification ← 8. Cleanup ← 9. User Availability
```

### Validation Steps
1. **File Format**: Check .xlsx/.xls extension
2. **File Reading**: Attempt to read Excel content
3. **Column Detection**: Find phone number column
4. **Number Validation**: Validate each phone number
5. **Quality Check**: Ensure minimum 50% valid numbers
6. **Final Approval**: Accept or reject file

## 🚨 Error Handling

### Common Issues and Solutions

**1. File Format Error**
```
❌ Please upload an Excel file (.xlsx or .xls)
```
**Solution**: Use Excel format, not PDF or images

**2. Missing Caption**
```
❌ Country Name Required

Please add the country name as caption when sending the file.

Example:
Send Tunisia.xlsx with caption: "Tunisia"
```
**Solution**: Add country name as file caption

**3. Invalid Numbers**
```
❌ File Validation Failed

Too many invalid numbers. Only 30.5% are valid (minimum 50% required)
```
**Solution**: Clean up phone numbers in Excel file

**4. Country in Use**
```
⚠️ Cannot delete 'Tunisia' - 5 users are currently using numbers from this country.
```
**Solution**: Wait for users to finish or manually release numbers

## 📈 Benefits

### For Administrators
- **Easy Management**: Upload files directly through bot
- **Real-time Updates**: No server restart required
- **Quality Control**: Automatic validation ensures data quality
- **Safety Features**: Backups and rollback protection

### For Users
- **More Countries**: Easy addition of new countries
- **Updated Numbers**: Fresh number pools when files updated
- **Reliable Service**: Validated numbers ensure better success rates

### For System
- **Dynamic Scaling**: Add countries without code changes
- **Data Integrity**: Validation ensures clean data
- **Backup Protection**: Safe file operations
- **Audit Trail**: Complete logging of all operations

## 🔮 Future Enhancements

### Planned Features
1. **CSV Support**: Direct CSV file uploads
2. **Bulk Operations**: Upload multiple countries at once
3. **Number Analytics**: Detailed usage statistics per country
4. **Auto-Updates**: Scheduled file updates from external sources
5. **Number Validation**: Real-time number validation services
6. **Geographic Data**: Country flags and timezone information

### Advanced Features
1. **API Integration**: External number provider APIs
2. **Number Recycling**: Automatic number rotation
3. **Usage Analytics**: Detailed country performance metrics
4. **Custom Formats**: Support for different number formats
5. **Batch Processing**: Handle large files efficiently

## 📋 File Management Best Practices

### File Preparation
1. **Clean Data**: Remove duplicates and invalid numbers
2. **Consistent Format**: Use international format (+country code)
3. **Quality Check**: Verify numbers before upload
4. **Reasonable Size**: Keep files under 10MB for best performance

### Upload Strategy
1. **Test Files**: Start with small test files
2. **Backup Important**: Keep local backups of important files
3. **Update Gradually**: Update countries during low usage
4. **Monitor Results**: Check upload success and user feedback

### Maintenance
1. **Regular Updates**: Refresh country files periodically
2. **Usage Monitoring**: Track which countries need more numbers
3. **Quality Control**: Remove countries with poor success rates
4. **User Feedback**: Monitor user complaints about specific countries

---

**System Status**: ✅ Production Ready  
**Last Updated**: 2024-01-15  
**Version**: 2.0.0  
**Compatibility**: TaskTreasure OTP Bot v2.0+

## 📞 Support

For technical support or questions about the country file management system:
- Check logs for detailed error information
- Use `/countries` to verify system status
- Contact system administrator for database issues
- Review this documentation for common solutions
