import sqlite3

def print_bot_config():
    conn = sqlite3.connect('mr_hux_alpha_bot.db')
    cur = conn.cursor()
    try:
        print('bot_config schema:')
        cur.execute('PRAGMA table_info(bot_config)')
        for row in cur.fetchall():
            print(row)
        print('\nbot_config table:')
        cur.execute('SELECT * FROM bot_config')
        rows = cur.fetchall()
        for row in rows:
            print(row)
        if not rows:
            print('(empty)')
        # Try manual insert if empty
        if not rows:
            print('\nTrying manual insert...')
            try:
                cur.execute('INSERT INTO bot_config (alert_threshold, theme, auto_refresh, notifications) VALUES (?, ?, ?, ?)', (42, 'light', 0, 1))
                conn.commit()
                print('Manual insert succeeded.')
            except Exception as e:
                print(f'Manual insert failed: {e}')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        conn.close()

if __name__ == '__main__':
    print_bot_config() 