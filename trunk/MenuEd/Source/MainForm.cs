/*
 * 	MenuEd - Boktai 3 Tilemap Editor
 * 
 *  To do:
 *  - Scroll through blocks and tiles
 *  - Edit block - middle-click = set palette, right-click = copy tile
 *  - Way to specify addresses
 *  - Work with all tilemaps in game (does except for palettes which are unimportant)
 */

using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Windows.Forms;
using System.IO;
using System.Diagnostics; // for trace
using System.Runtime.InteropServices;

namespace MenuEd
{
	public partial class MainForm : Form
	{
		const int palette0Address = 0x828818;
		const int paletteDAddress = 0x83A244;
		const int paletteEAddress = 0x83A264;
		const int paletteFAddress = 0x83A284;
		
		int tileAddress = 0x70A230;//0x65211C; //0x70A230;
		int mapAddress = 0x70A14C + 0x3A2C;//0x656F54;//0x70A14C + 0x3A2C; //status menu (config = 3C2C)
		int blockAddress =0x70C1B0;//0x6560DC;//0x70C1B0;
		
		bool ROMLoaded = false;
		string ROMFile;
		
		Color[] palette0;
		Color[] paletteD;
		Color[] paletteE;
		Color[] paletteF;

		Image[] tiles0;
		Image[] tilesD;
		Image[] tilesE;
		Image[] tilesF;
		Image[] blocks;
		
		byte[] tileData;
		byte[] blockData;
		byte[] mapData;
		
		int selBlock = 0;
		int selTile = 0;
		
		int xFlip = 0;
		int yFlip = 0;
		
		public MainForm()
		{
			InitializeComponent();
		}
		
		void BOpenROMClick(object sender, EventArgs e)
		{
			//if(!ROMLoaded) {
				if(openROM.ShowDialog() == DialogResult.OK) {
					ROMFile = openROM.FileName;
					loadPalette();
					loadTiles();
					loadBlocks();
					loadMap();
					updateTiles();
					updateBlocks();
					updateMap();
					updateBlock();
					ROMLoaded = true;
				}
			//}
		}
		
		void BLoadMapClick(object sender, EventArgs e)
		{
			if(ROMLoaded) {
				tileAddress = Convert.ToInt32(tTileAddress.Text, 16);
				mapAddress = Convert.ToInt32(tMapAddress.Text, 16);
				blockAddress = Convert.ToInt32(tBlockAddress.Text, 16);
				loadPalette();
				loadTiles();
				loadBlocks();
				loadMap();
				updateTiles();
				updateBlocks();
				updateMap();
				updateBlock();
			}
		}
		
		void BSaveROMClick(object sender, EventArgs e)
		{
			if(ROMLoaded) {
				saveROM.FileName = ROMFile;
				if(saveROM.ShowDialog() == DialogResult.OK) {
					saveBlocks();
					saveMap();
				}
			} else {
				//nothing to save message
			}
		}
		
		void PTilesPaint(object sender, System.Windows.Forms.PaintEventArgs e)
		{
			if(ROMLoaded)
				drawTiles(e.Graphics);
		}
		
		void PBlocksPaint(object sender, System.Windows.Forms.PaintEventArgs e)
		{
			if(ROMLoaded)
				drawBlocks(e.Graphics);
		}
		
		void PMapPaint(object sender, System.Windows.Forms.PaintEventArgs e)
		{
			if(ROMLoaded)
				drawMap(e.Graphics);
		}
		
		void PBlockPaint(object sender, System.Windows.Forms.PaintEventArgs e)
		{
			if(ROMLoaded)
				drawBlock(e.Graphics);
		}
		
		void PMapMouseDown(object sender, System.Windows.Forms.MouseEventArgs e)
		{
			if(ROMLoaded) {
				if(e.Button == MouseButtons.Right)
					BlockSelect(sender, e);
				else {
					int bx = e.X / 17;
					int by = e.Y / 17;
					int idx = (by * 16) + bx;
					mapData[idx * 2] = Convert.ToByte(selBlock & 0xFF);
					mapData[(idx * 2) + 1] = Convert.ToByte(selBlock >> 8);
					updateMap();
				}
			}
		}
		
		void PBlockMouseDown(object sender, System.Windows.Forms.MouseEventArgs e)
		{
			int bx, by, idx, palette, attrib;
			bx = e.X / 33;
			by = e.Y / 33;
			idx = ((by * 2) + bx) * 2;
			
			switch(e.Button) {
				case MouseButtons.Middle:
					palette = blockData[(selBlock * 8) + idx + 1] >> 4;
					Trace.WriteLine(Convert.ToString(palette, 16));
					palette = (palette + 1) % 0xF;
					attrib = (palette << 4) | (yFlip << 3) | (xFlip << 2) | (selTile >> 8);
					
					blockData[(selBlock * 8) + idx] = Convert.ToByte(selTile & 0xFF);
					blockData[(selBlock * 8) + idx + 1] = Convert.ToByte(attrib);
					
					blocks = toBlocks(blockData);
					updateBlock();
					updateBlocks();
					updateMap();
					break;
				case MouseButtons.Right:
					Graphics g = pTiles.CreateGraphics();
					Pen p = new Pen(pBlocks.BackColor);
					int rx = (selTile % 32) * 9;
					int ry = (selTile / 32) * 9;
					g.DrawRectangle(p, rx, ry, 9, 9); //erase old rectangle
					p.Dispose();
					
					selTile = blockData[(selBlock * 8) + idx] | ((blockData[(selBlock * 8) + idx + 1] & 3) << 8);
					drawTiles(g);
					g.Dispose();
					break;
				default:
					palette = blockData[(selBlock * 8) + idx + 1] >> 4;
					attrib = (palette << 4) | (yFlip << 3) | (xFlip << 2) | (selTile >> 8);
					
					blockData[(selBlock * 8) + idx] = Convert.ToByte(selTile & 0xFF);
					blockData[(selBlock * 8) + idx + 1] = Convert.ToByte(attrib);
					
					blocks = toBlocks(blockData);
					updateBlock();
					updateBlocks();
					updateMap();
					break;
			}
		}
		
		void FormKey(object sender, System.Windows.Forms.KeyEventArgs e)
		{
			xFlip = e.Shift ? 1 : 0;
			yFlip = e.Control ? 1 : 0;
		}
		
		void BlockSelect(object sender, System.Windows.Forms.MouseEventArgs e)
		{
			if(ROMLoaded) {
				Graphics g = pBlocks.CreateGraphics();
				Pen p = new Pen(pBlocks.BackColor);
				int rx = (selBlock % 16) * 17;
				int ry = (selBlock / 16) * 17;
				g.DrawRectangle(p, rx, ry, 17, 17); //erase old rectangle
				p.Dispose();
				
				int bx = e.X / 17;
				int by = e.Y / 17;
				if(sender == pMap) {
					int idx = (by * 16) + bx;
					selBlock = mapData[idx * 2] | (mapData[(idx * 2) + 1] << 8);
				} else {
					selBlock = (by * 16) + bx;
				}
				//Trace.WriteLine("Block selected: " + selBlock);
				drawBlocks(g);
				g.Dispose();
				updateBlock();
			}
		}
		
		void TileSelect(object sender, System.Windows.Forms.MouseEventArgs e)
		{
			if(ROMLoaded) {
				Graphics g = pTiles.CreateGraphics();
				Pen p = new Pen(pBlocks.BackColor);
				int rx = (selTile % 32) * 9;
				int ry = (selTile / 32) * 9;
				g.DrawRectangle(p, rx, ry, 9, 9); //erase old rectangle
				p.Dispose();
				
				int bx = e.X / 9;
				int by = e.Y / 9;
				selTile = (by * 32) + bx;
				drawTiles(g);
				g.Dispose();
			}
		}
		
		#region Drawing
		
		void updateTiles() {
			Graphics g = pTiles.CreateGraphics();
			drawTiles(g);
			g.Dispose();
		}
		
		void updateBlocks() {
			Graphics g = pBlocks.CreateGraphics();
			drawBlocks(g);
			g.Dispose();
		}
		
		void updateMap() {
			Graphics g = pMap.CreateGraphics();
			drawMap(g);
			g.Dispose();
		}
		
		void updateBlock() {
			Graphics g = pBlock.CreateGraphics();
			drawBlock(g);
			g.Dispose();
		}
		
		void drawTiles(Graphics g)
		{
			for(int x = 0; x < 32; x++) {
				for(int y = 0; y < 8; y++) {
					g.DrawImageUnscaled(tilesF[(y * 32) + x], (x * 9) + 1, (y * 9) + 1);
				}
			}
			
			Pen p = new Pen(Color.Blue);
			int rx = (selTile % 32) * 9;
			int ry = (selTile / 32) * 9;
			g.DrawRectangle(p, rx, ry, 9, 9);
			p.Dispose();
		}
		
		void drawBlocks(Graphics g)
		{
			for(int x = 0; x < 16; x++) {
				for(int y = 0; y < 16; y++) {
					g.DrawImageUnscaled(blocks[(y * 16) + x], (x * 17) + 1, (y * 17) + 1);
				}
			}
			
			Pen p = new Pen(Color.Blue);
			int rx = (selBlock % 16) * 17;
			int ry = (selBlock / 16) * 17;
			g.DrawRectangle(p, rx, ry, 17, 17);
			p.Dispose();
		}
		
		void drawMap(Graphics g)
		{
			int idx = 0;
			for(int y = 0; y < 16; y++) {
				for(int x = 0; x < 16; x++) {
					int block = mapData[idx * 2] | (mapData[(idx * 2) + 1] << 8);
					try {
						g.DrawImageUnscaled(blocks[block], (x * 17) + 1, (y * 17) + 1);
					} catch {
						Trace.WriteLine("Err: " + block);
					}
					idx++;
				}
			}
		}
		
		void drawBlock(Graphics g)
		{
			g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.None;
			int idx = 0;
			for(int y = 1; y < 67; y+=33) {
				for(int x = 1; x < 67; x+=33) {
					int attrib = blockData[(selBlock * 8) + idx + 1];
					int tn = blockData[(selBlock * 8) + idx] | ((attrib & 3) << 8);
					int xflip = (attrib >> 2) & 1;
					int yflip = (attrib >> 3) & 1;
					int palette = attrib >> 4;
					Image tmp;
					switch(palette) {
						case 0x0:
							tmp = (Image) tiles0[tn].Clone();
							break;
						case 0xD:
							tmp = (Image) tilesD[tn].Clone();
							break;
						case 0xE:
							tmp = (Image) tilesE[tn].Clone();
							break;
						case 0xF:
							tmp = (Image) tilesF[tn].Clone();
							break;
						default:
							//Trace.WriteLine("Other palette: " + Convert.ToString(palette, 16));
							tmp = (Image) tilesF[tn].Clone();
							break;
					}
					Image xf = (Image) tmp.Clone();
					xf.RotateFlip(RotateFlipType.RotateNoneFlipX);
					Image tmp2 = (Image)(xflip == 1 ? xf.Clone() : tmp.Clone());
					Image yf = (Image) tmp2.Clone();
					yf.RotateFlip(RotateFlipType.RotateNoneFlipY);
					Image tile = (Image)(yflip == 1 ? yf.Clone() : tmp2.Clone());
					
					g.DrawImage(tile, x, y, 32, 32);
					
					xf.Dispose();
					tmp.Dispose();
					tmp2.Dispose();
					yf.Dispose();
					tile.Dispose();
					idx += 2;
				}
			}
		}
		
		#endregion
		
		#region Data Loading/Saving
		
		void loadPalette() {
			FileStream fs = new FileStream(ROMFile, FileMode.Open);
			BinaryReader br = new BinaryReader(fs);
			fs.Seek(palette0Address, SeekOrigin.Begin);
			byte[] tmp = br.ReadBytes(32);
			palette0 = toPalette(tmp);
			fs.Seek(paletteDAddress, SeekOrigin.Begin);
			tmp = br.ReadBytes(32);
			paletteD = toPalette(tmp);
			fs.Seek(paletteEAddress, SeekOrigin.Begin);
			tmp = br.ReadBytes(32);
			paletteE = toPalette(tmp);
			fs.Seek(paletteFAddress, SeekOrigin.Begin);
			tmp = br.ReadBytes(32);
			paletteF = toPalette(tmp);
			fs.Dispose();
		}
		
		void loadTiles() {
			FileStream fs = new FileStream(ROMFile, FileMode.Open);
			BinaryReader br = new BinaryReader(fs);
			fs.Seek(tileAddress, SeekOrigin.Begin);
			tileData = br.ReadBytes(32 * 0x400);
			tiles0 = toTiles(tileData, palette0);
			tilesD = toTiles(tileData, paletteD);
			tilesE = toTiles(tileData, paletteE);
			tilesF = toTiles(tileData, paletteF);
			fs.Dispose();
		}
		
		void loadBlocks() {
			FileStream fs = new FileStream(ROMFile, FileMode.Open);
			BinaryReader br = new BinaryReader(fs);
			fs.Seek(blockAddress, SeekOrigin.Begin);
			blockData = br.ReadBytes(8 * 0x200);
			blocks = toBlocks(blockData);
			fs.Dispose();
		}
		
		void loadMap() {
			FileStream fs = new FileStream(ROMFile, FileMode.Open);
			BinaryReader br = new BinaryReader(fs);
			fs.Seek(mapAddress, SeekOrigin.Begin);
			mapData = br.ReadBytes(2 * 0x100);
			fs.Dispose();
		}
		
		void saveBlocks() {
			FileStream fs = new FileStream(ROMFile, FileMode.Open);
			BinaryWriter bw = new BinaryWriter(fs);
			fs.Seek(blockAddress, SeekOrigin.Begin);
			bw.Write(blockData);
			bw.Flush();
			fs.Dispose();
		}
		
		void saveMap() {
			FileStream fs = new FileStream(ROMFile, FileMode.Open);
			BinaryWriter bw = new BinaryWriter(fs);
			fs.Seek(mapAddress, SeekOrigin.Begin);
			bw.Write(mapData);
			bw.Flush();
			fs.Dispose();
		}
		
		#endregion
		
		#region Data Conversion
		
		Color[] toPalette(byte[] data) {
			Color[] ret = new Color[16];
			for(int i = 0; i < 16; i++) {
				int t1 = data[i * 2];
				int t2 = data[(i * 2) + 1];
				int red = (t1 & 0x1F) << 3; //bitmask to get red
				int green = (((t2 & 3) << 3) | (t1 >> 5)) << 3;
				int blue = ((t2 >> 2) & 0x1F) << 3; //bitmask in case last bit isn't 0
				//Trace.WriteLine(red.ToString() + "," + green.ToString() + "," + blue.ToString());
				ret[i] = Color.FromArgb(255, red, green, blue);
			}
			return ret;
		}
		
		Bitmap[] toTiles(byte[] data, Color[] palette) {
			Bitmap[] ret = new Bitmap[0x400];
			for(int i = 0; i < 0x400; i++) {
				Bitmap cur = new Bitmap(8, 8);
				int idx = 0;
				for(int y = 0; y < 8; y++) {
					for(int x = 0; x < 8; x+=2) {
						//Trace.WriteLine("(" + x + ", " + y + "): " + paletteF[data[idx] & 0xF].ToString());
						cur.SetPixel(x, y, palette[data[(i * 32) + idx] & 0xF]);
						cur.SetPixel(x + 1, y, palette[data[(i * 32) + idx] >> 4]);
						idx++;
					}
				}
				ret[i] = cur;
			}
			
			/*BitmapData bd = ret.LockBits(new Rectangle(0, 0, 8, 8), ImageLockMode.WriteOnly, PixelFormat.Format16bppRgb555);
			byte* bData = (byte *) bd.Scan0.ToPointer();
			for(int i = 0; i < 32; i++) {
				bData[i] = data[i];
			}
			ret.UnlockBits(bd);*/
			
			return ret;
		}
		
		Bitmap[] toBlocks(byte[] data) {
			Bitmap[] ret = new Bitmap[0x200];
			for(int i = 0; i < 0x200; i++) {
				Bitmap cur = new Bitmap(16, 16);
				Graphics g = Graphics.FromImage(cur);
				int idx = 0;
				for(int y = 0; y < 16; y+=8) {
					for(int x = 0; x < 16; x+=8) {
						int attrib = data[(i * 8) + idx + 1];
						int tn = data[(i * 8) + idx] | ((attrib & 3) << 8);
						int xflip = (attrib >> 2) & 1;
						int yflip = (attrib >> 3) & 1;
						int palette = attrib >> 4;
						Image tmp;
						switch(palette) {
							case 0x0:
								tmp = (Image) tiles0[tn].Clone();
								break;
							case 0xD:
								tmp = (Image) tilesD[tn].Clone();
								break;
							case 0xE:
								tmp = (Image) tilesE[tn].Clone();
								break;
							case 0xF:
								tmp = (Image) tilesF[tn].Clone();
								break;
							default:
								//Trace.WriteLine("Other palette: " + Convert.ToString(palette, 16));
								tmp = (Image) tilesF[tn].Clone();
								break;
						}
						Image xf = (Image) tmp.Clone();
						xf.RotateFlip(RotateFlipType.RotateNoneFlipX);
						Image tmp2 = (Image)(xflip == 1 ? xf.Clone() : tmp.Clone());
						Image yf = (Image) tmp2.Clone();
						yf.RotateFlip(RotateFlipType.RotateNoneFlipY);
						Image tile = (Image)(yflip == 1 ? yf.Clone() : tmp2.Clone());
							
						g.DrawImageUnscaled(tile, x , y);
						
						xf.Dispose();
						tmp.Dispose();
						tmp2.Dispose();
						yf.Dispose();
						tile.Dispose();
						idx += 2;
					}
				}
				g.Dispose();
				ret[i] = cur;
			}
			return ret;
		}
		
		#endregion
	}
	
}
