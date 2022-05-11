#! /usr/bin/env bash

sudo yum -y update
sudo yum -y groupinstall "Development Tools"
sudo yum -y install lzma gdbm gdbm-devel zlib* zlib-devel bzip2 bzip2-devel db4-devel libpcap-devel libuuid-devel libffi-devel tk tkinter tk-devel libbz2-dev readline-devel  sqlite sqlite-devel libsqlite3x-devel openssl-devel make xz xz-devel libffi-devel

# install libressl
ssl_tar=/usr/local/src/libressl-2.7.4.tar.gz
ssl_untar=/usr/local/src/libressl-2.7.4
if [[ ! -e $ssl_tar ]];then
    wget "https://ftp.openbsd.org/pub/OpenBSD/LibreSSL/libressl-2.7.4.tar.gz" -O $ssl_tar
fi

tar -zxvf $ssl_tar -C /usr/local/src
cd $ssl_untar
./configure --prefix=/usr/local
make && make install

touch /etc/ld.so.conf.d/local.conf
echo "/usr/local/src" >> /etc/ld.so.conf.d/local.conf
ldconfig -v

# install gcc version8.3
gcc_version=$(gcc --version 2>/dev/null)
if [[ -z $gcc_version || $(echo $gcc_version | sed '2,$d' | awk '{print $3}') < 8  ]];then
    yum -y install centos-release-scl
    yum -y install devtoolset-8-gcc devtoolset-8-gcc-c++ devtoolset-8-binutils
    scl enable devtoolset-7 bash

    echo "source /opt/rh/devtoolset-8/enable" >>/etc/profile
fi

src_path=/usr/local/src/Python-3.8.6.tar.xz
src_untar=/usr/local/src/Python-3.8.6
if [[ ! -e $src_path ]]; then
    wget "https://www.python.org/ftp/python/3.8.6/Python-3.8.6.tar.xz" -O $src_path
fi

tar -xvf $src_path -C /usr/local/src 

cd $src_untar
./configure --enable-optimizations

make && make install

rm -rf $src_untar $src_path $ssl_tar $ssl_untar
