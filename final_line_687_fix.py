#!/usr/bin/env python3

"""
FINAL LINE 687-689 INDENTATION FIX
This script will fix the persistent if statement indentation issue
"""

def fix_line_687_indentation():
    """Fix the specific if statement indentation issue at line 687-689"""
    
    with open('telegram_number_bot.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the problematic if statement around line 687
    for i, line in enumerate(lines):
        if 'if await self.is_user_approved(user_id):' in line:
            print(f"Found if statement at line {i+1}")
            
            # Fix the keyboard definition and subsequent lines
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith('# Check if user is in cooldown'):
                current_line = lines[j]
                
                # Fix specific patterns that should be inside the if block
                if 'keyboard = [' in current_line and not current_line.startswith('            '):
                    lines[j] = '            keyboard = [\n'
                    print(f"Fixed line {j+1}: keyboard definition")
                
                elif '[KeyboardButton(' in current_line and not current_line.startswith('                '):
                    lines[j] = '                ' + current_line.lstrip()
                    print(f"Fixed line {j+1}: keyboard button")
                
                elif ']' in current_line and 'KeyboardButton' not in current_line and not current_line.startswith('            '):
                    lines[j] = '            ]\n'
                    print(f"Fixed line {j+1}: closing bracket")
                
                elif 'reply_markup = ReplyKeyboardMarkup(' in current_line and not current_line.startswith('            '):
                    lines[j] = '            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)\n'
                    print(f"Fixed line {j+1}: reply_markup")
                
                elif 'welcome_message = f"""' in current_line and not current_line.startswith('            '):
                    lines[j] = '            welcome_message = f"""\n'
                    print(f"Fixed line {j+1}: welcome_message")
                
                elif 'await update.message.reply_text(' in current_line and not current_line.startswith('            '):
                    lines[j] = '            await update.message.reply_text(\n'
                    print(f"Fixed line {j+1}: reply_text call")
                
                elif 'welcome_message,' in current_line and not current_line.startswith('                '):
                    lines[j] = '                welcome_message,\n'
                    print(f"Fixed line {j+1}: welcome_message parameter")
                
                elif 'reply_markup=reply_markup' in current_line and not current_line.startswith('                '):
                    lines[j] = '                reply_markup=reply_markup\n'
                    print(f"Fixed line {j+1}: reply_markup parameter")
                
                elif 'return' in current_line and not current_line.startswith('            '):
                    lines[j] = '            return\n'
                    print(f"Fixed line {j+1}: return statement")
                
                j += 1
            
            break
    
    # Write the fixed content back
    with open('telegram_number_bot.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Line 687-689 indentation fix completed!")

if __name__ == "__main__":
    fix_line_687_indentation()
