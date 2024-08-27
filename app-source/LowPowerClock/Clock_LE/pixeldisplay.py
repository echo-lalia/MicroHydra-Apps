import framebuf, math

class PixelDisplay:
    """
    This class operates as a sub-display.
    It creates a retro, pixel-art style look in a window.
    """
    def __init__(
        self,
        display,
        width=32,
        height=30,
        px_size=4,
        color=46518,
        ):
        
        bufsize = ((math.ceil(width/8)*8) * height) // 8
        
        self.buf = framebuf.FrameBuffer(bytearray(bufsize), width, height, framebuf.MONO_HLSB)
        self.px_size = px_size
        self.width = width
        self.height = height
        self.color = color
        self.display = display
        
    def draw(self, x, y):
        self._draw(
                x, y,
                self.width, self.height,
                self.color
                )
                
    @micropython.viper      
    def _draw(self, start_x:int, start_y:int, width:int, height:int, color:int):
        px_size = int(self.px_size)
        buf = self.buf
        display = self.display
        
        # iterate over our pixels, and draw them!
        for px_y in range(height):
            for px_x in range(width):
                if buf.pixel(px_x, px_y):
                    display.fill_rect(
                        start_x + (px_x * px_size),
                        start_y + (px_y * px_size),
                        px_size, px_size,
                        color
                        )
    
    def fill(self, color):
        self.buf.fill(color)
        
    def line(self, *args):
        self.buf.line(*args)
        
    def rect(self, *args):
        self.buf.rect(*args)
        
    def text(self, *args):
        self.buf.text(*args)
    
    def center_text(self, text, x, y, color):
        x -= len(text) * 4
        self.buf.text(text,x,y,color)
    
    def ellipse(self, *args):
        self.buf.ellipse(*args)
        
    def pixel(self, *args):
        self.buf.pixel(*args)