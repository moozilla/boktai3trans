/*
 * Created by SharpDevelop.
 * User: Benjamin Harris
 * Date: 7/15/2007
 * Time: 2:22 PM
 * 
 * To change this template use Tools | Options | Coding | Edit Standard Headers.
 */
namespace MenuEd
{
	partial class MainForm
	{
		/// <summary>
		/// Designer variable used to keep track of non-visual components.
		/// </summary>
		private System.ComponentModel.IContainer components = null;
		
		/// <summary>
		/// Disposes resources used by the form.
		/// </summary>
		/// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
		protected override void Dispose(bool disposing)
		{
			if (disposing) {
				if (components != null) {
					components.Dispose();
				}
			}
			base.Dispose(disposing);
		}
		
		/// <summary>
		/// This method is required for Windows Forms designer support.
		/// Do not change the method contents inside the source code editor. The Forms designer might
		/// not be able to load this method if it was changed manually.
		/// </summary>
		private void InitializeComponent()
		{
			System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(MainForm));
			this.openROM = new System.Windows.Forms.OpenFileDialog();
			this.bOpenROM = new System.Windows.Forms.Button();
			this.pTiles = new System.Windows.Forms.PictureBox();
			this.gTiles = new System.Windows.Forms.GroupBox();
			this.gBlocks = new System.Windows.Forms.GroupBox();
			this.pBlocks = new System.Windows.Forms.PictureBox();
			this.gMap = new System.Windows.Forms.GroupBox();
			this.pMap = new System.Windows.Forms.PictureBox();
			this.bSaveROM = new System.Windows.Forms.Button();
			this.saveROM = new System.Windows.Forms.SaveFileDialog();
			this.gBlock = new System.Windows.Forms.GroupBox();
			this.pBlock = new System.Windows.Forms.PictureBox();
			this.bLoadMap = new System.Windows.Forms.Button();
			this.tBlockAddress = new System.Windows.Forms.TextBox();
			this.tMapAddress = new System.Windows.Forms.TextBox();
			this.tTileAddress = new System.Windows.Forms.TextBox();
			((System.ComponentModel.ISupportInitialize)(this.pTiles)).BeginInit();
			this.gTiles.SuspendLayout();
			this.gBlocks.SuspendLayout();
			((System.ComponentModel.ISupportInitialize)(this.pBlocks)).BeginInit();
			this.gMap.SuspendLayout();
			((System.ComponentModel.ISupportInitialize)(this.pMap)).BeginInit();
			this.gBlock.SuspendLayout();
			((System.ComponentModel.ISupportInitialize)(this.pBlock)).BeginInit();
			this.SuspendLayout();
			// 
			// openROM
			// 
			this.openROM.Filter = "GBA ROMS (*.gba)|*.gba|All Files (*.*)|*.*";
			// 
			// bOpenROM
			// 
			this.bOpenROM.Location = new System.Drawing.Point(12, 333);
			this.bOpenROM.Name = "bOpenROM";
			this.bOpenROM.Size = new System.Drawing.Size(75, 23);
			this.bOpenROM.TabIndex = 0;
			this.bOpenROM.Text = "Open ROM";
			this.bOpenROM.UseVisualStyleBackColor = true;
			this.bOpenROM.Click += new System.EventHandler(this.BOpenROMClick);
			this.bOpenROM.KeyUp += new System.Windows.Forms.KeyEventHandler(this.FormKey);
			this.bOpenROM.KeyDown += new System.Windows.Forms.KeyEventHandler(this.FormKey);
			// 
			// pTiles
			// 
			this.pTiles.BackColor = System.Drawing.Color.Gray;
			this.pTiles.Location = new System.Drawing.Point(6, 19);
			this.pTiles.Name = "pTiles";
			this.pTiles.Size = new System.Drawing.Size(289, 73);
			this.pTiles.TabIndex = 1;
			this.pTiles.TabStop = false;
			this.pTiles.MouseDown += new System.Windows.Forms.MouseEventHandler(this.TileSelect);
			this.pTiles.Paint += new System.Windows.Forms.PaintEventHandler(this.PTilesPaint);
			// 
			// gTiles
			// 
			this.gTiles.Controls.Add(this.pTiles);
			this.gTiles.Location = new System.Drawing.Point(287, 316);
			this.gTiles.Name = "gTiles";
			this.gTiles.Size = new System.Drawing.Size(301, 98);
			this.gTiles.TabIndex = 2;
			this.gTiles.TabStop = false;
			this.gTiles.Text = "Tiles";
			// 
			// gBlocks
			// 
			this.gBlocks.Controls.Add(this.pBlocks);
			this.gBlocks.Location = new System.Drawing.Point(303, 12);
			this.gBlocks.Name = "gBlocks";
			this.gBlocks.Size = new System.Drawing.Size(285, 298);
			this.gBlocks.TabIndex = 3;
			this.gBlocks.TabStop = false;
			this.gBlocks.Text = "Blocks";
			// 
			// pBlocks
			// 
			this.pBlocks.BackColor = System.Drawing.Color.Gray;
			this.pBlocks.Location = new System.Drawing.Point(6, 19);
			this.pBlocks.Name = "pBlocks";
			this.pBlocks.Size = new System.Drawing.Size(273, 273);
			this.pBlocks.TabIndex = 1;
			this.pBlocks.TabStop = false;
			this.pBlocks.MouseDown += new System.Windows.Forms.MouseEventHandler(this.BlockSelect);
			this.pBlocks.Paint += new System.Windows.Forms.PaintEventHandler(this.PBlocksPaint);
			// 
			// gMap
			// 
			this.gMap.Controls.Add(this.pMap);
			this.gMap.Location = new System.Drawing.Point(12, 12);
			this.gMap.Name = "gMap";
			this.gMap.Size = new System.Drawing.Size(285, 298);
			this.gMap.TabIndex = 4;
			this.gMap.TabStop = false;
			this.gMap.Text = "Map";
			// 
			// pMap
			// 
			this.pMap.BackColor = System.Drawing.Color.Gray;
			this.pMap.Location = new System.Drawing.Point(6, 19);
			this.pMap.Name = "pMap";
			this.pMap.Size = new System.Drawing.Size(273, 273);
			this.pMap.TabIndex = 1;
			this.pMap.TabStop = false;
			this.pMap.MouseDown += new System.Windows.Forms.MouseEventHandler(this.PMapMouseDown);
			this.pMap.Paint += new System.Windows.Forms.PaintEventHandler(this.PMapPaint);
			// 
			// bSaveROM
			// 
			this.bSaveROM.Location = new System.Drawing.Point(12, 362);
			this.bSaveROM.Name = "bSaveROM";
			this.bSaveROM.Size = new System.Drawing.Size(75, 23);
			this.bSaveROM.TabIndex = 0;
			this.bSaveROM.Text = "Save ROM";
			this.bSaveROM.UseVisualStyleBackColor = true;
			this.bSaveROM.Click += new System.EventHandler(this.BSaveROMClick);
			this.bSaveROM.KeyUp += new System.Windows.Forms.KeyEventHandler(this.FormKey);
			this.bSaveROM.KeyDown += new System.Windows.Forms.KeyEventHandler(this.FormKey);
			// 
			// saveROM
			// 
			this.saveROM.Filter = "GBA ROMS (*.gba)|*.gba|All Files (*.*)|*.*";
			// 
			// gBlock
			// 
			this.gBlock.Controls.Add(this.pBlock);
			this.gBlock.Location = new System.Drawing.Point(201, 316);
			this.gBlock.Name = "gBlock";
			this.gBlock.Size = new System.Drawing.Size(80, 98);
			this.gBlock.TabIndex = 5;
			this.gBlock.TabStop = false;
			this.gBlock.Text = "Block";
			// 
			// pBlock
			// 
			this.pBlock.BackColor = System.Drawing.Color.Gray;
			this.pBlock.Location = new System.Drawing.Point(6, 19);
			this.pBlock.Name = "pBlock";
			this.pBlock.Size = new System.Drawing.Size(67, 67);
			this.pBlock.TabIndex = 1;
			this.pBlock.TabStop = false;
			this.pBlock.MouseDown += new System.Windows.Forms.MouseEventHandler(this.PBlockMouseDown);
			this.pBlock.Paint += new System.Windows.Forms.PaintEventHandler(this.PBlockPaint);
			// 
			// bLoadMap
			// 
			this.bLoadMap.Location = new System.Drawing.Point(12, 391);
			this.bLoadMap.Name = "bLoadMap";
			this.bLoadMap.Size = new System.Drawing.Size(75, 23);
			this.bLoadMap.TabIndex = 0;
			this.bLoadMap.Text = "Load Map";
			this.bLoadMap.UseVisualStyleBackColor = true;
			this.bLoadMap.Click += new System.EventHandler(this.BLoadMapClick);
			this.bLoadMap.KeyUp += new System.Windows.Forms.KeyEventHandler(this.FormKey);
			this.bLoadMap.KeyDown += new System.Windows.Forms.KeyEventHandler(this.FormKey);
			// 
			// tBlockAddress
			// 
			this.tBlockAddress.Location = new System.Drawing.Point(93, 393);
			this.tBlockAddress.Name = "tBlockAddress";
			this.tBlockAddress.Size = new System.Drawing.Size(100, 20);
			this.tBlockAddress.TabIndex = 11;
			this.tBlockAddress.Text = "70C1B0";
			// 
			// tMapAddress
			// 
			this.tMapAddress.Location = new System.Drawing.Point(93, 364);
			this.tMapAddress.Name = "tMapAddress";
			this.tMapAddress.Size = new System.Drawing.Size(100, 20);
			this.tMapAddress.TabIndex = 10;
			this.tMapAddress.Text = "70DB78";
			// 
			// tTileAddress
			// 
			this.tTileAddress.Location = new System.Drawing.Point(93, 335);
			this.tTileAddress.Name = "tTileAddress";
			this.tTileAddress.Size = new System.Drawing.Size(100, 20);
			this.tTileAddress.TabIndex = 9;
			this.tTileAddress.Text = "70A230";
			// 
			// MainForm
			// 
			this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
			this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
			this.ClientSize = new System.Drawing.Size(599, 422);
			this.Controls.Add(this.tBlockAddress);
			this.Controls.Add(this.tMapAddress);
			this.Controls.Add(this.tTileAddress);
			this.Controls.Add(this.gBlock);
			this.Controls.Add(this.gMap);
			this.Controls.Add(this.gBlocks);
			this.Controls.Add(this.gTiles);
			this.Controls.Add(this.bSaveROM);
			this.Controls.Add(this.bLoadMap);
			this.Controls.Add(this.bOpenROM);
			this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle;
			this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
			this.Name = "MainForm";
			this.Text = "MenuEd";
			this.KeyUp += new System.Windows.Forms.KeyEventHandler(this.FormKey);
			this.KeyDown += new System.Windows.Forms.KeyEventHandler(this.FormKey);
			((System.ComponentModel.ISupportInitialize)(this.pTiles)).EndInit();
			this.gTiles.ResumeLayout(false);
			this.gBlocks.ResumeLayout(false);
			((System.ComponentModel.ISupportInitialize)(this.pBlocks)).EndInit();
			this.gMap.ResumeLayout(false);
			((System.ComponentModel.ISupportInitialize)(this.pMap)).EndInit();
			this.gBlock.ResumeLayout(false);
			((System.ComponentModel.ISupportInitialize)(this.pBlock)).EndInit();
			this.ResumeLayout(false);
			this.PerformLayout();
		}
		private System.Windows.Forms.TextBox tTileAddress;
		private System.Windows.Forms.TextBox tMapAddress;
		private System.Windows.Forms.TextBox tBlockAddress;
		private System.Windows.Forms.Button bLoadMap;
		private System.Windows.Forms.PictureBox pBlock;
		private System.Windows.Forms.GroupBox gBlock;
		private System.Windows.Forms.SaveFileDialog saveROM;
		private System.Windows.Forms.Button bSaveROM;
		private System.Windows.Forms.PictureBox pBlocks;
		private System.Windows.Forms.GroupBox gBlocks;
		private System.Windows.Forms.PictureBox pMap;
		private System.Windows.Forms.GroupBox gMap;
		private System.Windows.Forms.GroupBox gTiles;
		private System.Windows.Forms.PictureBox pTiles;
		private System.Windows.Forms.Button bOpenROM;
		private System.Windows.Forms.OpenFileDialog openROM;
	}
}
