# docker-PiPer-env

## 1. Preriminay
手順1: Dockerfileおよびrun.sh内で定義されている`USR_NAME`変数を任意のユーザー名で設定
<Dockerfile>
```ruby:Dockerfile
ARG USR_NAME=<任意のユーザー名>
```
<run.sh>
```ruby:run.sh
export USR_NAME=<任意のユーザー名>
```

手順2. dockerのコンテナをビルドする。
```
sh build.sh
```

手順3: run.shを実行し、イメージを立ち上げる。
```
sh run.sh
```

dockerイメージが起動すれば、初回設定は完了!

## 2. 1台だけロボットをロボットを動かすとき
### 2.1 準備
手順1: PiPERの電源を入れ、PCとUSB接続を行う。


手順2: run.shを実行し、イメージを立ち上げる。
```
sh run.sh
```

手順3: PiPERのSDKをダウンロード＆ROSをCmake (以下のオリジナルコマンドを実施。詳細はDockerfileのalias部分を参照)
```
set_sdk
```

手順4: PiPERのUSB接続(CAN)を認識しているか確認する。
```
sudo ethtool -i can0 | grep bus
```
※ロボット増やすごとにcanの番号が`can0, can1,...`と増えていく。コマンドを実行すると、`1-2:1.0`のようなポート番号が出力

手順5: USB接続が認識できたら、以下のコマンドでCANをアクティブ化。
```
bash can_activate.sh can0 1000000 "USBポート番号"
```
※コマンド最後のUSBポート番号は手順4で確認したものを使う

<補足>
CANの状態を確認/操作するのに便利なコマンドを以下に記載

CANの状態を確認(すべてのCANを同時表示)
```
ip link show
```
CANを停止
```
sudo ip link set can0 down
```
CANを立ち上げ
```
sudo ip link set can0 up
```

### 2.2 テストコード
#### 2.2.1 PiPERでグリッパーの開閉と手先を円軌道に動かす
以下のコマンドを実施
```
cd docker-PiPer-env/double_PiPer/src/test
python3 test_ctrlPiperJoint_can0.py
```
※コード中の`piper = Piper("can0")`を、動かしたいPiPERのCAN番号に揃える

can0~can3まではスクリプトを分けて用意
- python3 test_ctrlPiperJoint_can0.py
- python3 test_ctrlPiperJoint_can1.py
- python3 test_ctrlPiperJoint_can2.py
- python3 test_ctrlPiperJoint_can3.py

#### 2.2.2 PiPERの状態読み込み
手順1: dockerイメージ内で、rosを立ち上げる
```
roscore
```

手順2: 新しいterminalのタブを開き、起動済みのdockerイメージに入る
```
docker exec -it piper-env-image bash
sorc_devel
```
※`sorc_devel`コマンドは、ROSのcatkinファイルに移動して`source catkin/devel/setup.bash`を行う自作コマンド

手順3: PiPERのROSラウンチを立ち上げる
```
roslaunch piper start_master.launch can_port:=can1 auto_enable:=true
```
ここで、
`can_port`は、ノードを立ち上げるPiPERのCAN番号を変更するオプション(デフォルトは"can1")
`auto_enable`は、プログラムでPiPERを動かすために、PiPERのモードをチェンジするオプション

手順4: さらに、新しいterminalのタブを開き、起動済みのdockerイメージに入る
```
docker exec -it piper-env-image bash
sorc_devel
```

手順5: PiPERのJoint角度とグリッパー角度を公開するROSトピックの信号を可視化
```
rostopic echo /joint_grip_pos
```


## 3. 単腕でreader-follower遠隔制御
手順1: 以下のコマンドを実施して、dockerイメージを立ち上げ、CANをアクティブ
```
sh run.sh
set_sdk
sorc_devel

bash can_activate.sh "<reader側のCAN番号>" 1000000 "<reader側のUSBポート番号>"
bash can_activate.sh "<follower側のCAN番号>" 1000000 "<follower側のUSBポート番号>"

roscore
```
※CAN番号は`can0`や`can1`など。USBポート番号は`1-2:1.0`や`1-2:1.0`など


手順2: 2つ目のterminalを開き、ROSラウンチを立ち上げる。
```
docker exec -it piper-env-image bash
sorc_devel
roslaunch piper single_master_slave.launch can_slave_port:=can0 can_master_port:=can1 auto_enable:=true
```
ここで、
`can_slave_port`は、PiPER(follower側)のCAN番号を変更するオプション(デフォルトは"can0")
`can_master_port`は、PiPER(reader側)のCAN番号を変更するオプション(デフォルトは"can1")
`auto_enable`は、プログラムでPiPERを動かすために、PiPERのモードをチェンジするオプション

## 4. 双腕でreader-follower遠隔制御
手順1: 以下のコマンドを実施して、dockerイメージを立ち上げ、CANをアクティブ
```
sh run.sh
set_sdk
sorc_devel

bash can_activate.sh can0 1000000 "<右手のreader側のUSBポート番号>"
bash can_activate.sh can1 1000000 "<右手のfollower側のUSBポート番号>"
bash can_activate.sh can2 1000000 "<左手のreader側のUSBポート番号>"
bash can_activate.sh can3 1000000 "<左手のfollower側のUSBポート番号>"

roscore
```
※USBポート番号は`1-2:1.0`や`1-2:1.0`など


手順2: 2つ目のterminalを開き、ROSラウンチを立ち上げる。
```
docker exec -it piper-env-image bash
sorc_devel
roslaunch piper dual_master_slave.launch can_slave_R_port:=can0 can_master_R_port:=can1 can_slave_L_port:=can2 can_master_L_port:=can3 auto_enable:=true
```
ここで、
`can_slave_R_port`は、PiPER(右手のfollower側)のCAN番号を変更するオプション(デフォルトは"can0")
`can_master_R_port`は、PiPER(右手のreader側)のCAN番号を変更するオプション(デフォルトは"can1")
`can_slave_L_port`は、PiPER(左手のfollower側)のCAN番号を変更するオプション(デフォルトは"can2")
`can_master_L_port`は、PiPER(左手のreader側)のCAN番号を変更するオプション(デフォルトは"can3")
`auto_enable`は、プログラムでPiPERを動かすために、PiPERのモードをチェンジするオプション

### トラブルシューティング
ROSでcatkin_makeが実行できない場合は、以下のコマンドでlogを削除
```
rm -rf build/ devel/ log/
```

ROSのラウンチやトピックがうまく表示されないときは、rosのsetup.bashを再読込
```
sorc_devel
```