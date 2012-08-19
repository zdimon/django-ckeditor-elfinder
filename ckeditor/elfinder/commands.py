from ckeditor.settings import ELFINDER_ROOT, ELFINDER_URL, ELFINDER_THUMB
from ckeditor.elfinder import BaseCommand

import os
import hashlib


class OpenCommand(BaseCommand):
	''' open directory'''
	def config(self):
		self.options = {}
		self.optional = ['init', 'tree', 'target']	
	def execute(self):
		if self.init:
			self.execute_init()
		else:
			self.execute_open()
		self.execute_options()
		self.execute_upload_max_size()
		self.execute_api_ver()
		self.success = True
	def execute_init(self):
		path = self.find_path(self.target) or ELFINDER_ROOT 
		self.result['cwd'] = self.cwd(path)
		self.result['files'] = self.cdc(path)
		self.result['files'].append(self.get_dir_info(path))
		if path != os.path.abspath(ELFINDER_ROOT):
			self.result['files'].extend(self.cdc(ELFINDER_ROOT))
			self.result['files'].append(self.get_dir_info(ELFINDER_ROOT))	
	def execute_open(self):
		path = self.find_path(self.target) or ELFINDER_ROOT 
		self.result['cwd'] = self.cwd(path)
		self.result['files'] = self.cdc(path)
	def execute_options(self, **overwrite):
		self.options.update({
			'options':{
				'path':os.path.relpath(ELFINDER_ROOT, ELFINDER_ROOT),
				'url':ELFINDER_URL,
				'tmbUrl':'%s%s' %(ELFINDER_URL, 'tmb/'),
				'disabled':[u'ONN'],
				'seperator':'\\',
				'copyOverwrite':1,
				'archivers':{
					'create':self.get_archiveable(),
					'extract':self.get_extractable(),
				}
			},
		})
	def execute_api_ver(self, api="2.0"):
		self.api = {'api':api}
	def execute_upload_max_size(self, upload_max="2M"):
		self.upload_max = {'uplMaxSize':upload_max}
	def get_result(self):
		return (self.result, self.options, self.api, self.upload_max)
	
class FileCommand(BaseCommand):
	''' output file contents to the browser (download) '''
	def config(self):
		self.required = ['target']
		self.headers = {
			'Content-Disposition':'attachment; filename=foo.xls',
		}
		self.result_type=''
	def execute(self):
		path = self.find_path(self.target, resolution=True)
		f = open(path, 'rb')
		self.result = f.read()
		f.close()
		filename = os.path.basename(path)
		try:
			hs = hashlib.md5()
			hs.update(filename)
			hs.hexdigest()
		except:
			filename = u'%s.%s'%(self.hash(filename)[0:7],filename.rsplit('.', 1)[-1])
		self.headers = {'Content-Disposition':u'attachment; filename=%s'%filename}
		self.result_type = self.get_mime(path)[0]
		self.success = True
			
	
class ParentsCommand(BaseCommand):
	''' add to return child directories (not a command but option? todo) '''
	def config(self):
		self.required = ['target']
	def execute(self):
		path = os.path.abspath(self.find_path(self.target))
		self.result.update({
			'tree':self.get_parents(path)
		})
		self.success = True
	def get_parents(self, cwd):
		l = []
		vparent = os.path.dirname(ELFINDER_ROOT)
		path = os.path.abspath(cwd)
		while path != os.path.abspath(vparent):
			if path == os.path.abspath(ELFINDER_ROOT):
				l.append(self.cwd(path, True))
			else:
				l.append(self.cwd(path))
			path = os.path.dirname(path)
		return l
		
	
class TreeCommand(BaseCommand):
	''' add to return parent directories (not a command but option? todo) '''
	def config(self):
		self.required = ['target']
	def execute(self):
		path = self.find_path(self.target)
		self.result.update({
			'tree':self.filtering(path)
		})
		self.result['tree'].append(self.cwd(path))
		self.success = True
		
class LsCommand(BaseCommand):
	''' list files in directory (not a command but option? todo) '''
	def config(self):
		self.required = ['target']
	def execute(self):
		path = self.find_path(self.target)
		self.result.update({
			'list':os.listdir(path)
		})
		self.success = True
	
class TmbCommand(BaseCommand):
	''' create thumbnails for selected files '''
	pass
	
class SizeCommand(BaseCommand):
	''' return size for selected files '''
	def config(self):
		self.required = ['targets']
	def execute(self):
		self.result = 0
		for target in self.targets:
			path = self.find_path(target)
			try:
				path = unicode(path, 'utf8')
			except:
				pass
			if path:
				self.result += self.get_size(path)
		self.result = {'size':self.result}
		self.success = True
class DimCommand(BaseCommand):
	''' return image dimensions '''
	def config(self):
		self.required = ['target']
	def validate(self):
		if not self.imglib:
			self.can_execute = False
			self.errors = ['errCmdNoSupport']
	def execute(self):
		path = self.find_path(self.target)
		size = 'unknown'
		try:
			import Image
			image = Image.open(path)
			size = '%dx%d'%image.size
			self.success = True
			self.result['dim'] = size
		except:
			self.success = False
				
	
class MkdirCommand(BaseCommand):
	''' create directory '''
	def config(self):	
		self.required = ['target', 'name']
	def execute(self):
		target_folder = self.find_path(self.target)
		self.result['added'] = []
		if not self.check_name(self.name):
			self.success = False
			self.errors = ['errMkdir', '#%s'%self.target, 'errInvName']
		if not self.file_exists(target_folder, self.name):
			full_path = os.path.join(target_folder, self.name)
			os.mkdir(full_path)
			self.result['added'].append(self.get_dir_info(full_path))
			self.success = True
		else:
			self.success = False
			self.errors.extend(['errMkdir', self.name, 'errExists', self.name])
	
class MkfileCommand(BaseCommand):
	''' create text file '''
	def config(self):
		self.required = ['target', 'name']
	def execute(self):
		target_folder = self.find_path(self.target)
		self.result['added'] = []
		if not self.check_name(self.name):
			self.success = False
			self.errors = ['errMkfile', '#%s'%self.target, 'errInvName']
		if not self.file_exists(target_folder, self.name):
			full_path = os.path.join(target_folder, self.name)
			f = open(full_path, 'w')
			f.close()
			self.result['added'].append(self.get_file_info(full_path))
			self.success = True
		else:
			self.success = False
			self.errors.extend(['errMkfile', self.name, 'errExists', self.name])
		
		
			
	
class RmCommand(BaseCommand):
	''' delete file '''
	def config(self):	
		self.required = ['targets']
	def execute(self):
		self.result['removed'] = []
		for target in self.targets:
			path = self.find_path(target)
			try:
				path = unicode(path, 'utf8')
			except:
				pass
			if os.path.isfile(path):
				os.remove(path)
				self.result['removed'].append(target)
				self.success = True
			else:
				if self.remove_dir(path):
					self.result['removed'].append(target)
					self.success = True
				
	def remove_dir(self, path):
		try:
			os.rmdir(path)
			return True
		except:
			if self.force_remove(path):
				try:
					os.rmdir(path)
					return True
				except:
					self.errors = ['errRm', os.path.basename(path)]
					return False
			else:
				self.errors = ['errRm', os.path.basename(path)]
		return True
	def force_remove(self, dir):
		#remove the directory even is its not empty
		for curdir, dirs, files in os.walk(dir):
			for f in files:
				os.remove(os.path.join(curdir, f))
			for d in dirs:
				d = os.path.join(curdir, d)
				if not os.listdir(d):
					os.rmdir(d)
			if not os.listdir(curdir):
				os.rmdir(curdir)
		return True
class RenameCommand(BaseCommand):
	''' rename file '''
	def config(self):
		self.required = ['target', 'name']
	def execute(self):
		target_path = self.find_path(self.target, resolution=True)
		self.result['added'] = []
		if not self.check_name(self.name):
			self.success = False
			self.errors = ['errRename', '#%s'%self.target, 'errInvName']
		elif not self.file_exists(os.path.dirname(target_path), self.name):
			try:
				new_path = os.path.join(os.path.dirname(target_path), self.name)
				os.rename(target_path, new_path)
				self.success = True
				if os.path.isdir(new_path):
					self.result['added'].append(self.get_dir_info(new_path))
				else:
					self.result['added'].append(self.get_file_info(new_path))
				self.result['removed'] = [self.target]
			except Exception, e:
				self.success = False
				self.errors = ['errRename', '#%s'%self.target, 'errUnknown']
		else:
			self.success = False
			exists = os.path.abspath(os.path.join(os.path.dirname(target_path), self.name))
			self.errors = ['errRename', '#%s'%self.target, 'errExists', self.name]

	
class DuplicateCommand(BaseCommand):
	''' create copy of file '''
	def config(self):
		self.required = ['targets']
	def execute(self):
		self.result['added'] = []
		for target in self.targets:
			path = self.find_path(target, resolution=True)
			new_path = self.unique_name(path)
			if self.safe_copy(path, new_path):
				self.result['added'].append(self.get_info(new_path))
				self.success = True
			else:
				self.errors = ['errCopy', u'#%s'%target]
				self.success = False
	def unique_name(self, path, add=' copy '):
		dir = os.path.dirname(path)
		name = os.path.basename(path)
		basic_name = name #for directories
		ext = ''
		if not os.path.isdir(path):
			name_com = name.split('.')
			l = len(name_com)
			if l == 2:
				basic_name, ext = tuple(name_com)
			if l == 1:
				basic_name = name_com[0]
			if l > 2:
				if name_com[-1] in ['bz', 'bz2', 'gz']:
					if name_com[-2] in ['tar']:
						basic_name, ext = (u'.'.join(name_com[0:-2]), '.'.join(name_com[-2:]))
				else:
					basic_name, ext = (u'.'.join(name_com[0:-1]), name_com[-1])
		basic_name = basic_name.split(add, 1)[0]
		available_names = [n for n in os.listdir(dir) if n.startswith(basic_name) and add in n]
		i = 1
		if available_names:
			available_names.sort()
			last_name = available_names[-1]
			last_name = last_name.split(add)
			last_name = last_name[-1].strip()
			if ext:
				last_name = last_name.split(ext)[0].split('.')[0]
			try:
				i = int(last_name)
				i += 1
			except:
				pass
		new_name = u'%s%s%d.%s'%(basic_name, add, i, ext)
		if os.path.isdir(path):
			new_name = u'%s%s%d'%(basic_name, add, i)
		new_path = os.path.join(dir, new_name)
		return new_path
			
	
class PasteCommand(BaseCommand):
	''' copy or move files '''
	def config(self):
		self.required = ['targets', 'src', 'dst']
		self.optional = ['cut']
	def validate(self):
		try:
			if self.cut[0] == '1':
				self.cut = True
			else:
				self.cut = False
		except:
			self.cut = False
	def execute(self):
		destnation = self.find_path(self.dst, resolution=True)
		source = self.find_path(self.src, resolution=True)
		self.result['added'] = []
		self.result['removed'] = []
		for target in self.targets:
			path = self.find_path(target, resolution=True)
			new_path = os.path.abspath(os.path.join(destnation, os.path.basename(path)))
			if self.cut:
				try:
					os.rename(path, new_path)
					if os.path.isdir(new_path):
						self.result['added'].append(self.get_dir_info(new_path))
					else:
						self.result['added'].append(self.get_file_info(new_path))
					self.result['removed'].append(target)
					self.success = True
					continue
				except:
					self.errors = ['errMove', u'#%s'%target]
					self.success = False
			else:
				if self.safe_copy(path, new_path):
					if os.path.isdir(new_path):
						self.result['added'].append(self.get_dir_info(new_path))
					else:
						self.result['added'].append(self.get_file_info(new_path))
					self.result['removed'].append(target)
					self.success = True
					continue
				else:
					self.errors = ['errMove', u'#%s'%target]
					self.success = False
	def safe_copy(self, src, dst):
		import shutil
		if os.path.isfile(src):
			try:
				shutil.copyfile(src, dst)
				shutil.copymode(src, dst)
				return True
			except:
				return False
		elif os.path.isdir(src):
			try:
				os.mkdir(dst)
			except:
				return False
			for f in os.listdir(src):
				new_src = os.path.join(src, f)
				new_dist = os.path.join(dst, f)
				if not self.safe_copy(new_src, new_dist):
					return False
		return True
					
				

class UploadCommand(BaseCommand):
	''' upload file '''
	def config(self):
		self.required = ['target', 'upload']
	def execute(self):	
		uploaded_list = []
		self.result['added'] = []
		self.result['removed'] = []
		path = self.find_path(self.target, resolution=True)
		for f in self.upload:
			file_name = f.name
			full_path = os.path.join(path, file_name)
			if self.file_exists(path, file_name):
				self.result['removed'].append(self.hash(full_path))
			try:
				import codecs
				temp = codecs.open(full_path, 'wb', encoding='utf8')
				for chunk in f.chunks():
					temp.write(chunk)
				temp.close()
			except:
				temp = open(full_path, 'wb')
				for chunk in f.chunks():
					temp.write(chunk)
				temp.close()
			uploaded_list.append(full_path)
		for ufile in uploaded_list:
			self.result['added'].append(self.get_info(ufile))
		self.success = True
				
	
class GetCommand(BaseCommand):
	''' return text file contents '''
	def config(self):
		self.required = ['target']
	def execute(self):
		path = self.find_path(self.target, resolution=True)
		if not os.path.isfile(path):
			self.success = False
			self.errors = ['errGet', u'#%s'%self.target]
		else:
			import codecs
			f = codecs.open(path, encoding='utf8')
			self.result['content'] = f.read()
			f.close()
			self.success = True
	
class PutCommand(BaseCommand):
	''' save text file '''
	def config(self):
		self.required = ['target']
		self.optional = ['content']
	def validate(self):
		self.content = self.content[0]
	def execute(self):
		path = self.find_path(self.target, resolution=True)
		import codecs
		try:
			f = codecs.open(path, 'wb+', encoding='utf8')
			f.write(self.content)
			f.close()
		except:
			f = open(path, 'wb+')
			f.write(self.content)
			f.close()
		self.result['changed'] = [self.get_info(path)]
		self.success = True
	
class ArchiveCommand(BaseCommand):
	''' create archive '''
	def config(self):
		self.required = ['targets', 'type']
	def validate(self):
		if self.type not in self.get_archiveable():
			self.can_execute = False
			self.errors = ['errArcType', 'errArchive']
	def execute(self):
		targets_list = [self.find_path(target, resolution=True) for target in self.targets]
		cwd = os.path.dirname(targets_list[0])
		new_archive = self.archive(cwd, self.type, targets_list)
		if new_archive:
			self.result['added'] = [self.get_info(new_archive)]
			self.success = True
		
	def archive(self, current, arch_type, targets):
		err = {}
		extensions = {
			'application/zip':'.zip',
			'application/x-tar':'.tar',
			'application/x-7z-compressed':'.7z',
			'application/x-gzip':'.tar.gz',
			'application/x-bzip2':'.tar.bz2',
			}
		name = u'new_archive'
		from datetime import datetime
		new_archive = os.path.abspath(os.path.join(current, u'%s_%s'%(name, datetime.now().strftime('%d-%m-%Y@%I_%M_%p'))))
		ext = extensions[arch_type]
		path = None
		if ext:
			new_archive += ext
		else:
			self.errors = ['errArchive', 'errArcType']
			return None
		if os.path.exists(new_archive):
			self.errors = ['errArchive', 'errExists', os.path.basename(new_archive), u'try to rename your current Archive first.']
			return None
			
		if ext == '.tar':
			path = self.build_tar_archive(current, new_archive, targets)
		elif ext == '.zip':
			path = self.build_zip_archive(current, new_archive, targets)
		elif ext == '.rar':
			path = self.build_rar_archive(current, new_archive, targets)
		elif ext == '.tar.bz2':
			path = self.build_tar_archive(current, new_archive, targets, bzip2 = True)
		elif ext == '.tar.gz':
			path = self.build_tar_archive(current, new_archive, targets, gzip=True)
		else:
			self.errors = ['errArchive', 'errArcType']
			return None
		return path
	def build_zip_archive(self, current, new_archive, targets):
		import zipfile
		err = {}
		curdir = os.getcwd()
		os.chdir(current)
		new_zip = zipfile.ZipFile(new_archive, mode='w')
		for target in targets:
			if os.path.isfile(target):
				new_zip.write(target, arcname=os.path.basename(target))
				continue
			elif os.path.isdir(target):
				for cdir, dirs, files in os.walk(target):
					for f in files:
						fp = os.path.join(cdir, f)
						fd = os.path.relpath(fp, start=current).replace('\\', '/')
						new_zip.write(fp, arcname=fd)
		new_zip.close()
		os.chdir(curdir)
		return new_archive
	def build_tar_archive(self, current, new_archive, targets, gzip=False, bzip2=False):
		import tarfile as tar
		curdir = os.getcwd()
		os.chdir(current)
		mode = 'w'
		if gzip:
			mode = 'w:gz'
		elif bzip2:
			mode = 'w:bz2'
		new_tar = tar.open(os.path.basename(new_archive), mode=mode)
		for target in targets:
			target = os.path.basename(target)
			new_tar.encoding = 'utf8'
			new_tar.format = tar.PAX_FORMAT
			new_tar.add(target, arcname=target)
		new_tar.close()
		os.chdir(curdir)
		return new_archive
	
class ExtractCommand(BaseCommand):
	''' extract archive '''
	def config(self):
		self.required = ['target']
	def execute(self):
		self.result['added'] = []
		self.result['removed'] = []
		path = self.find_path(self.target, resolution=True)
		from datetime import datetime 
		ext_dir = os.path.abspath(os.path.join(os.path.dirname(path), u'%s_%s'%(os.path.basename(path), datetime.now().strftime('%d-%m-%Y@%I_%M_%p'))))
		os.mkdir(ext_dir)
		extracted = self.extract(path, ext_dir)
		if extracted:
			self.result['added'].append(self.get_info(ext_dir))
		else:
			self.errors = ['errExtract', '#%s'%self.target]
		self.success = extracted
	def extract_arc(self, target, current, zip=False, rar=False):
		tar = None
		if not zip and not rar:
			import tarfile
			tar = tarfile.open(target)
		elif zip:
			import zipfile
			tar = zipfile.ZipFile(target)
		elif rar:
			import rarfile
			tar = rarfile.RarFile(target)
		try:
			tar.extractall(path=current)
		except Exception, e:
			return False
		return True
		
	def extract(self, target, current):
		'''Extract target archive'''
		extracters = {
			'.tar':self.extract_arc,
			'.gz':self.extract_arc,
			'.bz2':self.extract_arc,
			'.zip':self.extract_arc,
			}
		arcname = os.path.basename(target)
		ext = os.path.splitext(arcname)[1]
		if not ext in extracters:
			self.errors = ['errExtract', u'#%s'%self.target, 'errArcType']
			return err
		zip = {'zip':False}
		if ext == '.zip':
			zip = {'zip':True}
		extract_method = extracters[ext]
		extracted = apply(extract_method, (target, current), zip)
		return extracted
class SearchCommand(BaseCommand):
	''' search for files '''
	def config(self):
		self.required = ['q']
	def execute(self):
		self.result['files'] = []
		for path in self.get_match_list(self.q):
			self.result['files'].append(self.get_info(path))
		self.success = True
	def get_match_list(self, q):
		l = []
		parent_path = u'%s'%ELFINDER_ROOT
		for dirpath, dirnames, filenames in os.walk(parent_path):
			if os.path.abspath(dirpath) == ELFINDER_THUMB:
				continue
			fl = [os.path.abspath(os.path.join(dirpath, f)) for f in filenames if q.lower() in f.lower()]
			dl = [os.path.abspath(os.path.join(dirpath, d)) for d in dirnames if q.lower() in d.lower()]
			l.extend(fl)
			l.extend(dl)
		return l
		
	
class InfoCommand(BaseCommand):
	''' return info for selected files '''
	def config(self):
		self.required = ['targets']
	def execute(self):
		self.result['files'] = []
		for target in self.targets:
			path = self.find_path(target, resolution=True)
			self.result['files'].append(self.get_info(path))
		self.success = True
class ResizeCommand(BaseCommand):
	''' resize target image '''
	def config(self):
		self.required = ['width', 'height', 'mode', 'target']
		self.optional = ['x', 'y']
	def validate_params(self):
		super(ResizeCommand, self).validate_params()
		try:
			self.width = int(self.width)
			self.height = int(self.height)
			self.x = int(self.x)
			self.y = int(self.y)
		except:
			pass
	def execute(self):
		path = self.find_path(self.target, resolution=True)
		import Image
		image = Image.open(path)
		if self.mode == 'resize':
			image = image.resize((self.width, self.height), 1)
		else:
			image = image.crop((self.x, self.y, self.width, self.height))
		image.save(path)
		self.result['changed'] = [self.get_info(path)]
		self.success = True
	

COMMANDS_MAP = {
	'open' : OpenCommand,
	'file' : FileCommand,
	'tree' : TreeCommand,
	'parents' : ParentsCommand,
	'ls' : LsCommand,
	'tmb' : TmbCommand, 
	'size' : SizeCommand,
	'dim' : DimCommand,
	'mkdir' : MkdirCommand,
	'mkfile' : MkfileCommand,
	'rm' : RmCommand,
	'rename' : RenameCommand,
	'duplicate' : DuplicateCommand,
	'paste' : PasteCommand,
	'upload' : UploadCommand,
	'get' : GetCommand,
	'put' : PutCommand,
	'archive' : ArchiveCommand,
	'extract' : ExtractCommand,#TODO
	'search' : SearchCommand,
	'info' : InfoCommand,
	'resize' : ResizeCommand,
}