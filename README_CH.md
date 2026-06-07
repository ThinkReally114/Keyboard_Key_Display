<div align="center">

# Keyboard Key Display


一个 Linux 的桌面键盘按键显示器，可以在窗口未获得焦点时全局监听键盘输入，并用可视化键盘布局显示当前按下的按键。

启动时会请求权限，放心，我们的代码是无害的，你可以随意审查我们的代码

</div>


## 功能特性

- Linux 全局键盘监听，不需要应用窗口获得焦点。
- 可视化键盘布局。
- 按键按下高亮显示。
- 支持窗口置顶。
- 支持窗口透明度、圆角、边框颜色、按键颜色等配置。
- 支持自定义键盘布局。
- 支持无边框窗口，也支持系统原生标题栏窗口。

## 运行环境

- Linux 桌面环境。
- Python 3。
- tkinter。
- `/dev/input` 读取权限。

在 Debian / Ubuntu 上，如果缺少 tkinter，可以安装：

```bash
sudo apt install python3-tk
```

## 启动方式

进入项目目录：

```bash
#比如我在/home/thinkreally/work/keyb desket目录下运行
cd "/home/thinkreally/work/keyb desket"
./run.sh
```

也可以直接运行：

```bash
python3 key_display.py
```

如果当前用户没有 `/dev/input` 读取权限，`run.sh` 会自动使用 `sudo -E python3 key_display.py` 启动。

## 关闭方式

- 点击窗口关闭按钮。
- 按 `Ctrl + Q` 退出应用。
- 如果窗口异常无法关闭，可以在终端执行：

```bash
sudo pkill -f key_display.py
```

## 配置文件

应用外观和布局通过 `config.json` 配置。

### window

| 字段 | 说明 |
| --- | --- |
| `alpha` | 窗口透明度，范围 `0.0` 到 `1.0` |
| `always_on_top` | 是否置顶窗口 |
| `corner_radius` | 窗口圆角半径 |
| `frameless` | 是否使用无边框窗口，`true` 为无边框，`false` 为系统原生标题栏 |

### colors

| 字段 | 说明 |
| --- | --- |
| `background` | 主背景色 |
| `border` | 窗口边框颜色 |
| `title_bar` | 自定义标题栏背景色 |
| `text` | 标题文字颜色 |
| `text_glow` | 预留高亮文字颜色 |
| `key_idle` | 按键默认文字颜色 |
| `key_active` | 按键按下时的背景/边框颜色 |
| `key_text` | 按键按下时的文字颜色 |
| `key_border` | 按键默认边框颜色 |
| `status_online` | 状态点颜色 |
| `close_button` | 关闭按钮颜色 |
| `close_button_hover` | 关闭按钮悬停颜色 |

### keyboard

| 字段 | 说明 |
| --- | --- |
| `layout` | 自定义键盘布局，二维数组，每个字符串代表一个按键 |
| `key_width` | 普通按键宽度 |
| `key_height` | 按键高度 |
| `key_padding` | 按键间距 |
| `key_radius` | 按键圆角半径 |
| `font_size` | 按键字体大小 |

示例：

```json
{
    "window": {
        "alpha": 0.2,
        "always_on_top": true,
        "corner_radius": 30,
        "frameless": false
    },
    "keyboard": {
        "layout": [
            ["Esc", "1", "2", "3", "Backspace"],
            ["Tab", "Q", "W", "E", "R"],
            ["Ctrl", "A", "S", "D", "Enter"]
        ],
        "key_width": 42,
        "key_height": 42,
        "key_padding": 3,
        "key_radius": 13,
        "font_size": 10
    }
}
```

## Wayland 和 X11 说明

- 我们仅在 Ubuntu 26.04 LTS Wayland 上测试过该应用。
- Wayland 对应用移动窗口、透明窗口、透明圆角有更严格限制。
- 如果你使用 Wayland，推荐把 `window.frameless` 设置为 `false`，使用系统原生标题栏移动和关闭窗口。
- 如果你使用 X11，可以尝试把 `window.frameless` 设置为 `true`，使用无边框窗口。
- tkinter 的 `alpha` 和透明圆角在 Wayland 下可能不会完全生效，这是傻逼的窗口管理器限制。

## 权限说明

全局监听键盘需要读取 `/dev/input/event*`，通常有两种方式：

- 使用 `sudo` 启动应用。
- 将当前用户加入 `input` 用户组。

加入 `input` 用户组示例：

```bash
sudo usermod -aG input $USER
```

执行后需要重新登录系统才会生效。

## 说明

谢谢你支持我的项目。

由于我不熟悉 GitHub，而且我只是初中生，我可能无法及时响应你的 Pull Request 和 Issue，请耐心等待。

如果问题比较复杂，我可能需要更多时间来解决。

（傻逼 Wayland 让我 bug++）
